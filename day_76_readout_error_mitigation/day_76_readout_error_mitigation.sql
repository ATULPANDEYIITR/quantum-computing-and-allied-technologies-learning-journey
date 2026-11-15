-- ============================================================
-- READOUT ERROR MITIGATION
-- Measurement Calibration, Correction and Audit Database
-- PostgreSQL 15+
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS readout;
SET search_path TO readout, public;

-- ------------------------------------------------------------
-- Enumerated domain states
-- ------------------------------------------------------------

CREATE TYPE calibration_status AS ENUM (
    'DRAFT',
    'ACTIVE',
    'STALE',
    'RETIRED',
    'INVALID'
);

CREATE TYPE experiment_status AS ENUM (
    'SUBMITTED',
    'VALIDATED',
    'PROCESSING',
    'CORRECTED',
    'FAILED'
);

CREATE TYPE correction_method AS ENUM (
    'LINEAR_INVERSION',
    'REGULARIZED_LEAST_SQUARES',
    'BAYESIAN'
);

CREATE TYPE audit_event_type AS ENUM (
    'CALIBRATION_CREATED',
    'CALIBRATION_ACTIVATED',
    'CALIBRATION_STALE',
    'EXPERIMENT_SUBMITTED',
    'EXPERIMENT_CORRECTED',
    'EXPERIMENT_FAILED',
    'POLICY_UPDATED'
);

-- ------------------------------------------------------------
-- Institutional and instrument entities
-- ------------------------------------------------------------

CREATE TABLE laboratories (
    laboratory_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    laboratory_name VARCHAR(150) NOT NULL UNIQUE,
    institution VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE instruments (
    instrument_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    laboratory_id BIGINT NOT NULL
        REFERENCES laboratories(laboratory_id),
    instrument_name VARCHAR(150) NOT NULL,
    hardware_model VARCHAR(120) NOT NULL,
    firmware_version VARCHAR(80),
    qubit_count INTEGER NOT NULL CHECK (qubit_count BETWEEN 1 AND 30),
    operational BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (laboratory_id, instrument_name)
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(254) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    role_name VARCHAR(50) NOT NULL
        CHECK (role_name IN (
            'RESEARCHER',
            'CALIBRATION_OPERATOR',
            'ADMINISTRATOR',
            'AUDITOR'
        )),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- Calibration campaigns
-- ------------------------------------------------------------

CREATE TABLE calibration_campaigns (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id BIGINT NOT NULL
        REFERENCES instruments(instrument_id),
    calibration_version INTEGER NOT NULL CHECK (calibration_version > 0),
    status calibration_status NOT NULL DEFAULT 'DRAFT',
    correction_method correction_method NOT NULL
        DEFAULT 'REGULARIZED_LEAST_SQUARES',
    num_qubits INTEGER NOT NULL CHECK (num_qubits BETWEEN 1 AND 30),
    regularization NUMERIC(16,12) NOT NULL DEFAULT 0.00000001
        CHECK (regularization >= 0),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    created_by BIGINT REFERENCES researchers(researcher_id),
    notes TEXT,
    UNIQUE (instrument_id, calibration_version),
    CHECK (
        completed_at IS NULL OR completed_at >= started_at
    ),
    CHECK (
        activated_at IS NULL OR completed_at IS NOT NULL
    )
);

-- Per-qubit measurement response probabilities.
-- Rows represent true prepared states.
-- Columns represent measured outcomes.
CREATE TABLE qubit_calibrations (
    qubit_calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    calibration_id BIGINT NOT NULL
        REFERENCES calibration_campaigns(calibration_id)
        ON DELETE CASCADE,
    qubit_index INTEGER NOT NULL CHECK (qubit_index >= 0),
    shots_prepared_zero INTEGER NOT NULL
        CHECK (shots_prepared_zero > 0),
    shots_prepared_one INTEGER NOT NULL
        CHECK (shots_prepared_one > 0),
    count_00 INTEGER NOT NULL CHECK (count_00 >= 0),
    count_01 INTEGER NOT NULL CHECK (count_01 >= 0),
    count_10 INTEGER NOT NULL CHECK (count_10 >= 0),
    count_11 INTEGER NOT NULL CHECK (count_11 >= 0),
    p00 NUMERIC(12,10) GENERATED ALWAYS AS (
        count_00::NUMERIC / shots_prepared_zero
    ) STORED,
    p10 NUMERIC(12,10) GENERATED ALWAYS AS (
        count_01::NUMERIC / shots_prepared_zero
    ) STORED,
    p01 NUMERIC(12,10) GENERATED ALWAYS AS (
        count_10::NUMERIC / shots_prepared_one
    ) STORED,
    p11 NUMERIC(12,10) GENERATED ALWAYS AS (
        count_11::NUMERIC / shots_prepared_one
    ) STORED,
    UNIQUE (calibration_id, qubit_index),
    CHECK (count_00 + count_01 = shots_prepared_zero),
    CHECK (count_10 + count_11 = shots_prepared_one)
);

-- ------------------------------------------------------------
-- Full correlated assignment matrices
-- ------------------------------------------------------------

CREATE TABLE assignment_matrix_entries (
    calibration_id BIGINT NOT NULL
        REFERENCES calibration_campaigns(calibration_id)
        ON DELETE CASCADE,
    measured_state VARCHAR(30) NOT NULL,
    true_state VARCHAR(30) NOT NULL,
    probability NUMERIC(16,12) NOT NULL
        CHECK (probability BETWEEN 0 AND 1),
    PRIMARY KEY (
        calibration_id,
        measured_state,
        true_state
    ),
    CHECK (measured_state ~ '^[01]+$'),
    CHECK (true_state ~ '^[01]+$'),
    CHECK (length(measured_state) = length(true_state))
);

-- ------------------------------------------------------------
-- Experiment and measurement entities
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id BIGINT NOT NULL
        REFERENCES instruments(instrument_id),
    calibration_id BIGINT NOT NULL
        REFERENCES calibration_campaigns(calibration_id),
    researcher_id BIGINT REFERENCES researchers(researcher_id),
    experiment_name VARCHAR(180) NOT NULL,
    num_qubits INTEGER NOT NULL CHECK (num_qubits BETWEEN 1 AND 30),
    total_shots BIGINT NOT NULL CHECK (total_shots > 0),
    status experiment_status NOT NULL DEFAULT 'SUBMITTED',
    method correction_method NOT NULL
        DEFAULT 'REGULARIZED_LEAST_SQUARES',
    regularization NUMERIC(16,12) NOT NULL DEFAULT 0.00000001
        CHECK (regularization >= 0),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,
    UNIQUE (experiment_id, calibration_id),
    CHECK (
        completed_at IS NULL OR completed_at >= submitted_at
    )
);

CREATE TABLE measurement_counts (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    bitstring VARCHAR(30) NOT NULL,
    measured_count BIGINT NOT NULL CHECK (measured_count >= 0),
    PRIMARY KEY (experiment_id, bitstring),
    CHECK (bitstring ~ '^[01]+$')
);

CREATE TABLE corrected_probabilities (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    basis_state VARCHAR(30) NOT NULL,
    raw_probability NUMERIC(16,12) NOT NULL
        CHECK (raw_probability BETWEEN 0 AND 1),
    corrected_probability NUMERIC(16,12) NOT NULL
        CHECK (corrected_probability BETWEEN 0 AND 1),
    PRIMARY KEY (experiment_id, basis_state)
);

CREATE TABLE experiment_diagnostics (
    experiment_id BIGINT PRIMARY KEY
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    residual_norm NUMERIC(20,12) NOT NULL
        CHECK (residual_norm >= 0),
    iterations INTEGER NOT NULL CHECK (iterations >= 0),
    converged BOOLEAN NOT NULL,
    condition_indicator NUMERIC(20,10),
    correction_runtime_ms NUMERIC(16,4)
        CHECK (correction_runtime_ms >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Operational policies
-- ------------------------------------------------------------

CREATE TABLE mitigation_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(150) NOT NULL UNIQUE,
    minimum_calibration_shots INTEGER NOT NULL
        CHECK (minimum_calibration_shots > 0),
    maximum_calibration_age_hours INTEGER NOT NULL
        CHECK (maximum_calibration_age_hours > 0),
    drift_threshold NUMERIC(8,6) NOT NULL
        CHECK (drift_threshold > 0 AND drift_threshold <= 1),
    require_convergence BOOLEAN NOT NULL DEFAULT TRUE,
    maximum_residual NUMERIC(16,10) NOT NULL
        CHECK (maximum_residual > 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE experiment_policy_assignments (
    experiment_id BIGINT PRIMARY KEY
        REFERENCES experiments(experiment_id),
    policy_id BIGINT NOT NULL
        REFERENCES mitigation_policies(policy_id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Audit records
-- ------------------------------------------------------------

CREATE TABLE audit_events (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type audit_event_type NOT NULL,
    calibration_id BIGINT REFERENCES calibration_campaigns(calibration_id),
    experiment_id BIGINT REFERENCES experiments(experiment_id),
    researcher_id BIGINT REFERENCES researchers(researcher_id),
    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------

CREATE INDEX idx_campaign_instrument_status
    ON calibration_campaigns(instrument_id, status);

CREATE INDEX idx_campaign_activation
    ON calibration_campaigns(instrument_id, activated_at DESC);

CREATE INDEX idx_experiment_status_date
    ON experiments(status, submitted_at DESC);

CREATE INDEX idx_experiment_calibration
    ON experiments(calibration_id);

CREATE INDEX idx_measurement_experiment
    ON measurement_counts(experiment_id);

CREATE INDEX idx_audit_created
    ON audit_events(created_at DESC);

CREATE INDEX idx_audit_event
    ON audit_events(event_type, created_at DESC);

CREATE INDEX idx_instrument_operational
    ON instruments(laboratory_id)
    WHERE operational = TRUE;

-- ------------------------------------------------------------
-- Audit trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION log_calibration_activation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'ACTIVE'
       AND OLD.status IS DISTINCT FROM 'ACTIVE' THEN

        INSERT INTO audit_events (
            event_type,
            calibration_id,
            event_details
        )
        VALUES (
            'CALIBRATION_ACTIVATED',
            NEW.calibration_id,
            jsonb_build_object(
                'version', NEW.calibration_version,
                'instrument_id', NEW.instrument_id
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calibration_activation
AFTER UPDATE ON calibration_campaigns
FOR EACH ROW
EXECUTE FUNCTION log_calibration_activation();

-- ------------------------------------------------------------
-- Calibration integrity trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_calibration_activation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    actual_count INTEGER;
    expected_count INTEGER;
    bad_count INTEGER;
BEGIN
    IF NEW.status = 'ACTIVE' AND OLD.status <> 'ACTIVE' THEN

        SELECT qubit_count
        INTO expected_count
        FROM instruments
        WHERE instrument_id = NEW.instrument_id;

        IF expected_count <> NEW.num_qubits THEN
            RAISE EXCEPTION
                'Calibration qubit count differs from instrument.';
        END IF;

        SELECT COUNT(*)
        INTO actual_count
        FROM qubit_calibrations
        WHERE calibration_id = NEW.calibration_id;

        IF actual_count <> NEW.num_qubits THEN
            RAISE EXCEPTION
                'Incomplete calibration: expected %, received %.',
                NEW.num_qubits, actual_count;
        END IF;

        SELECT COUNT(*)
        INTO bad_count
        FROM qubit_calibrations
        WHERE calibration_id = NEW.calibration_id
          AND (
              shots_prepared_zero < 100
              OR shots_prepared_one < 100
          );

        IF bad_count > 0 THEN
            RAISE EXCEPTION
                'Calibration has insufficient measurement samples.';
        END IF;

        NEW.completed_at := COALESCE(
            NEW.completed_at,
            CURRENT_TIMESTAMP
        );

        NEW.activated_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_calibration
BEFORE UPDATE OF status ON calibration_campaigns
FOR EACH ROW
EXECUTE FUNCTION validate_calibration_activation();

-- ------------------------------------------------------------
-- Measurement integrity trigger
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_measurement_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_length INTEGER;
BEGIN
    SELECT num_qubits
    INTO expected_length
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF length(NEW.bitstring) <> expected_length THEN
        RAISE EXCEPTION
            'Measurement bitstring length must equal %.',
            expected_length;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT OR UPDATE ON measurement_counts
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_count();

-- ------------------------------------------------------------
-- Calibration eligibility function
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_calibration_eligible(
    p_calibration_id BIGINT,
    p_minimum_shots INTEGER,
    p_maximum_age_hours INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    campaign calibration_campaigns%ROWTYPE;
    actual_count INTEGER;
    minimum_samples INTEGER;
BEGIN
    SELECT *
    INTO campaign
    FROM calibration_campaigns
    WHERE calibration_id = p_calibration_id;

    IF NOT FOUND OR campaign.status <> 'ACTIVE' THEN
        RETURN FALSE;
    END IF;

    IF campaign.activated_at <
       CURRENT_TIMESTAMP - make_interval(hours => p_maximum_age_hours)
    THEN
        RETURN FALSE;
    END IF;

    SELECT COUNT(*), COALESCE(MIN(
        LEAST(shots_prepared_zero, shots_prepared_one)
    ), 0)
    INTO actual_count, minimum_samples
    FROM qubit_calibrations
    WHERE calibration_id = p_calibration_id;

    RETURN actual_count = campaign.num_qubits
       AND minimum_samples >= p_minimum_shots;
END;
$$;

-- ------------------------------------------------------------
-- Measurement retrieval function
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_raw_probabilities(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    basis_state VARCHAR,
    probability NUMERIC
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    total_count NUMERIC;
BEGIN
    SELECT SUM(measured_count)
    INTO total_count
    FROM measurement_counts
    WHERE experiment_id = p_experiment_id;

    IF total_count IS NULL OR total_count <= 0 THEN
        RAISE EXCEPTION 'No measurement samples available.';
    END IF;

    RETURN QUERY
    SELECT
        mc.bitstring,
        mc.measured_count::NUMERIC / total_count
    FROM measurement_counts mc
    WHERE mc.experiment_id = p_experiment_id
    ORDER BY mc.bitstring;
END;
$$;

-- ------------------------------------------------------------
-- Experiment submission procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE submit_experiment(
    p_instrument_id BIGINT,
    p_calibration_id BIGINT,
    p_researcher_id BIGINT,
    p_name VARCHAR,
    p_shots BIGINT,
    p_counts JSONB,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_experiment_id BIGINT;
    v_num_qubits INTEGER;
    v_item RECORD;
BEGIN
    SELECT num_qubits
    INTO v_num_qubits
    FROM instruments
    WHERE instrument_id = p_instrument_id
      AND operational = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Instrument is unavailable.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM researchers
        WHERE researcher_id = p_researcher_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Researcher is not authorized.';
    END IF;

    IF NOT is_calibration_eligible(
        p_calibration_id, 1000, 24
    ) THEN
        RAISE EXCEPTION 'Calibration is not eligible.';
    END IF;

    IF p_shots <= 0 OR jsonb_typeof(p_counts) <> 'object' THEN
        RAISE EXCEPTION 'Invalid experiment input.';
    END IF;

    INSERT INTO experiments (
        instrument_id,
        calibration_id,
        researcher_id,
        experiment_name,
        num_qubits,
        total_shots
    )
    VALUES (
        p_instrument_id,
        p_calibration_id,
        p_researcher_id,
        p_name,
        v_num_qubits,
        p_shots
    )
    RETURNING experiment_id INTO v_experiment_id;

    FOR v_item IN
        SELECT key, value
        FROM jsonb_each(p_counts)
    LOOP
        INSERT INTO measurement_counts (
            experiment_id,
            bitstring,
            measured_count
        )
        VALUES (
            v_experiment_id,
            v_item.key,
            (v_item.value #>> '{}')::BIGINT
        );
    END LOOP;

    INSERT INTO experiment_policy_assignments (
        experiment_id,
        policy_id
    )
    VALUES (
        v_experiment_id,
        p_policy_id
    );

    INSERT INTO audit_events (
        event_type,
        experiment_id,
        researcher_id,
        event_details
    )
    VALUES (
        'EXPERIMENT_SUBMITTED',
        v_experiment_id,
        p_researcher_id,
        jsonb_build_object('shots', p_shots)
    );

    UPDATE experiments
    SET status = 'VALIDATED'
    WHERE experiment_id = v_experiment_id;

    RAISE NOTICE 'Experiment submitted: %', v_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- Merge-independent correction eligibility reporting view
-- ------------------------------------------------------------

CREATE VIEW calibration_eligibility_report AS
SELECT
    c.calibration_id,
    c.instrument_id,
    c.calibration_version,
    c.status,
    c.num_qubits,
    c.activated_at,
    COUNT(q.qubit_calibration_id) AS calibrated_qubits,
    MIN(
        LEAST(
            q.shots_prepared_zero,
            q.shots_prepared_one
        )
    ) AS minimum_qubit_shots,
    CASE
        WHEN c.status <> 'ACTIVE' THEN FALSE
        WHEN COUNT(q.qubit_calibration_id) <> c.num_qubits THEN FALSE
        WHEN c.activated_at <
            CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN FALSE
        ELSE TRUE
    END AS eligible
FROM calibration_campaigns c
LEFT JOIN qubit_calibrations q
    ON q.calibration_id = c.calibration_id
GROUP BY c.calibration_id;

CREATE VIEW experiment_performance_report AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.total_shots,
    d.residual_norm,
    d.iterations,
    d.converged,
    d.correction_runtime_ms,
    c.calibration_version,
    i.instrument_name
FROM experiments e
JOIN instruments i
    ON i.instrument_id = e.instrument_id
JOIN calibration_campaigns c
    ON c.calibration_id = e.calibration_id
LEFT JOIN experiment_diagnostics d
    ON d.experiment_id = e.experiment_id;

-- ------------------------------------------------------------
-- Sample data
-- ------------------------------------------------------------

INSERT INTO laboratories (
    laboratory_name,
    institution
)
VALUES (
    'Quantum Measurement Laboratory',
    'National Quantum Research Centre'
);

INSERT INTO instruments (
    laboratory_id,
    instrument_name,
    hardware_model,
    firmware_version,
    qubit_count
)
VALUES (
    1,
    'QPU-ALPHA',
    'Superconducting Processor',
    '3.2.1',
    2
);

INSERT INTO researchers (
    email,
    full_name,
    role_name
)
VALUES
(
    'operator@example.org',
    'Calibration Operator',
    'CALIBRATION_OPERATOR'
),
(
    'researcher@example.org',
    'Measurement Researcher',
    'RESEARCHER'
),
(
    'auditor@example.org',
    'Governance Auditor',
    'AUDITOR'
);

INSERT INTO mitigation_policies (
    policy_name,
    minimum_calibration_shots,
    maximum_calibration_age_hours,
    drift_threshold,
    require_convergence,
    maximum_residual
)
VALUES
(
    'STANDARD_READOUT_POLICY',
    1000,
    24,
    0.03,
    TRUE,
    0.05
),
(
    'STRICT_READOUT_POLICY',
    5000,
    6,
    0.01,
    TRUE,
    0.02
);

INSERT INTO calibration_campaigns (
    instrument_id,
    calibration_version,
    status,
    num_qubits,
    created_by
)
VALUES
(1, 1, 'DRAFT', 2, 1),
(1, 2, 'DRAFT', 2, 1);

-- Version 1: asymmetric measurement errors.
INSERT INTO qubit_calibrations (
    calibration_id,
    qubit_index,
    shots_prepared_zero,
    shots_prepared_one,
    count_00,
    count_01,
    count_10,
    count_11
)
VALUES
(1, 0, 10000, 10000, 9400, 600, 900, 9100),
(1, 1, 10000, 10000, 9600, 400, 700, 9300);

-- Version 2: a deliberately incomplete calibration.
INSERT INTO qubit_calibrations (
    calibration_id,
    qubit_index,
    shots_prepared_zero,
    shots_prepared_one,
    count_00,
    count_01,
    count_10,
    count_11
)
VALUES
(2, 0, 10000, 10000, 9500, 500, 500, 9500);

-- Activation of version 1 succeeds.
UPDATE calibration_campaigns
SET status = 'ACTIVE'
WHERE calibration_id = 1;

-- Incomplete activation fails if executed:
-- UPDATE calibration_campaigns
-- SET status = 'ACTIVE'
-- WHERE calibration_id = 2;

-- ------------------------------------------------------------
-- Experiment submission
-- ------------------------------------------------------------

CALL submit_experiment(
    1,
    1,
    2,
    'Bell-state readout experiment',
    50000,
    '{
        "00": 33600,
        "01": 4900,
        "10": 7500,
        "11": 4000
    }'::JSONB,
    1
);

-- ------------------------------------------------------------
-- Retrieval and evaluation queries
-- ------------------------------------------------------------

SELECT *
FROM calibration_eligibility_report
ORDER BY calibration_id;

SELECT *
FROM get_raw_probabilities(1);

SELECT
    experiment_id,
    SUM(measured_count) AS observed_shots
FROM measurement_counts
GROUP BY experiment_id;

-- Check probability normalization.
SELECT
    experiment_id,
    SUM(
        measured_count::NUMERIC /
        NULLIF(
            SUM(measured_count) OVER (
                PARTITION BY experiment_id
            ),
            0
        )
    ) AS probability_sum
FROM measurement_counts
GROUP BY experiment_id, measured_count;

-- Review asymmetric per-qubit readout performance.
SELECT
    calibration_id,
    qubit_index,
    p00,
    p11,
    1 - p00 AS zero_to_one_error,
    1 - p11 AS one_to_zero_error,
    (p00 + p11) / 2 AS balanced_readout_accuracy
FROM qubit_calibrations
ORDER BY calibration_id, qubit_index;

-- Aggregate calibration quality.
SELECT
    calibration_id,
    AVG((p00 + p11) / 2) AS mean_readout_accuracy,
    MIN(LEAST(p00, p11)) AS worst_correct_assignment
FROM qubit_calibrations
GROUP BY calibration_id;

-- Retrieve audit history.
SELECT
    audit_id,
    event_type,
    calibration_id,
    experiment_id,
    event_details,
    created_at
FROM audit_events
ORDER BY created_at;

-- ------------------------------------------------------------
-- Demonstrate a validated processing transaction
-- ------------------------------------------------------------

BEGIN;

UPDATE experiments
SET status = 'PROCESSING'
WHERE experiment_id = 1
  AND status = 'VALIDATED';

INSERT INTO experiment_diagnostics (
    experiment_id,
    residual_norm,
    iterations,
    converged,
    condition_indicator,
    correction_runtime_ms
)
VALUES (
    1,
    0.008500000000,
    450,
    TRUE,
    2.1000000000,
    15.7500
);

-- The SQL database records correction output supplied by
-- a trusted numerical correction service.
-- It does not execute the matrix optimization itself.

INSERT INTO corrected_probabilities (
    experiment_id,
    basis_state,
    raw_probability,
    corrected_probability
)
VALUES
(1, '00', 0.672000000000, 0.700000000000),
(1, '01', 0.098000000000, 0.100000000000),
(1, '10', 0.150000000000, 0.150000000000),
(1, '11', 0.080000000000, 0.050000000000);

-- Enforce normalized output.
DO $$
DECLARE
    probability_total NUMERIC;
BEGIN
    SELECT SUM(corrected_probability)
    INTO probability_total
    FROM corrected_probabilities
    WHERE experiment_id = 1;

    IF ABS(probability_total - 1.0) > 0.000001 THEN
        RAISE EXCEPTION
            'Corrected probability distribution is not normalized.';
    END IF;
END;
$$;

UPDATE experiments
SET
    status = 'CORRECTED',
    completed_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1;

INSERT INTO audit_events (
    event_type,
    experiment_id,
    event_details
)
VALUES (
    'EXPERIMENT_CORRECTED',
    1,
    jsonb_build_object(
        'method', 'REGULARIZED_LEAST_SQUARES',
        'residual', 0.0085
    )
);

COMMIT;

-- ------------------------------------------------------------
-- Final reporting
-- ------------------------------------------------------------

SELECT *
FROM experiment_performance_report;

SELECT
    e.experiment_id,
    e.experiment_name,
    COUNT(cp.basis_state) AS corrected_states,
    SUM(cp.raw_probability) AS raw_probability_sum,
    SUM(cp.corrected_probability) AS corrected_probability_sum,
    d.residual_norm,
    d.converged
FROM experiments e
LEFT JOIN corrected_probabilities cp
    ON cp.experiment_id = e.experiment_id
LEFT JOIN experiment_diagnostics d
    ON d.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    d.residual_norm,
    d.converged;

-- Failure-case reporting: experiments without successful correction.
SELECT
    experiment_id,
    experiment_name,
    status,
    failure_reason
FROM experiments
WHERE status = 'FAILED';

COMMIT;
