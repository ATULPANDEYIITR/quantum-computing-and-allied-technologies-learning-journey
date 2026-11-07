-- ============================================================
-- QUANTUM CONTROL AND PULSE CALIBRATION DATABASE
-- PostgreSQL 15+
--
-- Domain:
-- Qubits -> Hardware configurations -> Pulses
--        -> Pulse sequences -> Calibration experiments
--        -> Measurements -> Calibration decisions
--        -> Approved calibration versions
--        -> Execution records
--
-- All numerical pulse values use a documented unit convention.
-- This database is a control-workflow model, not a hardware driver.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_control;

SET search_path TO quantum_control, public;

-- ------------------------------------------------------------
-- 1. ENUMERATED DOMAIN STATES
-- ------------------------------------------------------------

CREATE TYPE qubit_status AS ENUM (
    'AVAILABLE',
    'MAINTENANCE',
    'DISABLED'
);

CREATE TYPE pulse_type AS ENUM (
    'X',
    'Y',
    'ARBITRARY',
    'IDLE'
);

CREATE TYPE experiment_type AS ENUM (
    'RABI',
    'RAMSEY',
    'T1',
    'T2',
    'AMPLITUDE_SWEEP',
    'PHASE_SWEEP'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE calibration_status AS ENUM (
    'PENDING',
    'PASSED',
    'FAILED',
    'REVOKED'
);

CREATE TYPE approval_status AS ENUM (
    'APPROVED',
    'REJECTED'
);

CREATE TYPE execution_status AS ENUM (
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

-- ------------------------------------------------------------
-- 2. USERS AND CONTROL ROLES
-- ------------------------------------------------------------

CREATE TABLE control_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    role_name VARCHAR(30) NOT NULL
        CHECK (
            role_name IN (
                'OPERATOR',
                'CALIBRATION_ENGINEER',
                'REVIEWER',
                'ADMINISTRATOR'
            )
        ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 3. QUBIT INVENTORY
-- ------------------------------------------------------------

CREATE TABLE qubits (
    qubit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id VARCHAR(100) NOT NULL UNIQUE,
    frequency_ghz NUMERIC(12,6) NOT NULL
        CHECK (frequency_ghz > 0),
    t1_us NUMERIC(14,6) NOT NULL
        CHECK (t1_us > 0),
    t2_us NUMERIC(14,6) NOT NULL
        CHECK (t2_us > 0 AND t2_us <= 2 * t1_us),
    status qubit_status NOT NULL DEFAULT 'AVAILABLE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- 4. HARDWARE CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE hardware_configs (
    hardware_config_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    config_name VARCHAR(120) NOT NULL UNIQUE,
    max_amplitude NUMERIC(14,8) NOT NULL
        CHECK (max_amplitude > 0),
    min_duration_us NUMERIC(14,8) NOT NULL
        CHECK (min_duration_us > 0),
    max_duration_us NUMERIC(14,8) NOT NULL,
    max_detuning_mhz NUMERIC(14,8) NOT NULL
        CHECK (max_detuning_mhz >= 0),
    max_pulses INTEGER NOT NULL DEFAULT 1000
        CHECK (max_pulses > 0),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (max_duration_us >= min_duration_us)
);

-- ------------------------------------------------------------
-- 5. PULSE DEFINITIONS
-- ------------------------------------------------------------

CREATE TABLE pulses (
    pulse_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pulse_name VARCHAR(120) NOT NULL,
    pulse_kind pulse_type NOT NULL,
    amplitude NUMERIC(14,8) NOT NULL
        CHECK (amplitude >= 0),
    duration_us NUMERIC(14,8) NOT NULL
        CHECK (duration_us > 0),
    phase_rad NUMERIC(14,8) NOT NULL DEFAULT 0,
    detuning_mhz NUMERIC(14,8) NOT NULL DEFAULT 0,
    created_by BIGINT REFERENCES control_users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (pulse_name, created_at)
);

-- ------------------------------------------------------------
-- 6. PULSE SEQUENCES
-- ------------------------------------------------------------

CREATE TABLE pulse_sequences (
    sequence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sequence_name VARCHAR(150) NOT NULL,
    qubit_id BIGINT NOT NULL REFERENCES qubits(qubit_id),
    created_by BIGINT REFERENCES control_users(user_id),
    sequence_version INTEGER NOT NULL DEFAULT 1
        CHECK (sequence_version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (qubit_id, sequence_name, sequence_version)
);

CREATE TABLE sequence_steps (
    sequence_step_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sequence_id BIGINT NOT NULL
        REFERENCES pulse_sequences(sequence_id) ON DELETE CASCADE,
    pulse_id BIGINT NOT NULL REFERENCES pulses(pulse_id),
    step_number INTEGER NOT NULL CHECK (step_number > 0),
    start_time_us NUMERIC(14,8) NOT NULL
        CHECK (start_time_us >= 0),
    UNIQUE (sequence_id, step_number),
    UNIQUE (sequence_id, start_time_us)
);

CREATE INDEX idx_sequence_steps_sequence
    ON sequence_steps(sequence_id, step_number);

-- ------------------------------------------------------------
-- 7. CALIBRATION EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE calibration_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    qubit_id BIGINT NOT NULL REFERENCES qubits(qubit_id),
    hardware_config_id BIGINT NOT NULL
        REFERENCES hardware_configs(hardware_config_id),
    experiment_kind experiment_type NOT NULL,
    experiment_status experiment_status NOT NULL DEFAULT 'CREATED',
    pulse_duration_us NUMERIC(14,8)
        CHECK (pulse_duration_us IS NULL OR pulse_duration_us > 0),
    target_amplitude NUMERIC(14,8)
        CHECK (target_amplitude IS NULL OR target_amplitude > 0),
    sample_count INTEGER NOT NULL DEFAULT 101
        CHECK (sample_count BETWEEN 3 AND 10001),
    created_by BIGINT REFERENCES control_users(user_id),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        completed_at IS NULL OR
        started_at IS NOT NULL AND completed_at >= started_at
    ),
    CHECK (
        experiment_status <> 'FAILED' OR
        failure_reason IS NOT NULL
    )
);

CREATE INDEX idx_experiments_qubit_status
    ON calibration_experiments(qubit_id, experiment_status);

CREATE INDEX idx_experiments_created
    ON calibration_experiments(created_at DESC);

-- ------------------------------------------------------------
-- 8. EXPERIMENT MEASUREMENTS
-- ------------------------------------------------------------

CREATE TABLE experiment_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES calibration_experiments(experiment_id)
        ON DELETE CASCADE,
    sample_number INTEGER NOT NULL CHECK (sample_number > 0),
    amplitude NUMERIC(14,8) NOT NULL CHECK (amplitude >= 0),
    delay_us NUMERIC(14,8) NOT NULL DEFAULT 0
        CHECK (delay_us >= 0),
    measured_probability NUMERIC(12,10) NOT NULL
        CHECK (measured_probability BETWEEN 0 AND 1),
    measurement_count INTEGER NOT NULL DEFAULT 1000
        CHECK (measurement_count > 0),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (experiment_id, sample_number)
);

CREATE INDEX idx_measurements_experiment
    ON experiment_measurements(experiment_id, sample_number);

-- ------------------------------------------------------------
-- 9. CALIBRATION RECORDS
-- ------------------------------------------------------------

CREATE TABLE calibration_records (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    qubit_id BIGINT NOT NULL REFERENCES qubits(qubit_id),
    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES calibration_experiments(experiment_id),
    calibration_version INTEGER NOT NULL
        CHECK (calibration_version > 0),
    pi_amplitude NUMERIC(14,8) NOT NULL
        CHECK (pi_amplitude > 0),
    pi_over_two_amplitude NUMERIC(14,8) NOT NULL
        CHECK (pi_over_two_amplitude > 0),
    excitation_error NUMERIC(12,10) NOT NULL
        CHECK (excitation_error BETWEEN 0 AND 1),
    fidelity_threshold NUMERIC(12,10) NOT NULL
        CHECK (fidelity_threshold BETWEEN 0 AND 1),
    calibration_status calibration_status NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (qubit_id, calibration_version),
    CHECK (
        abs(pi_over_two_amplitude - pi_amplitude / 2)
        <= 0.000001
    )
);

CREATE INDEX idx_calibration_qubit_version
    ON calibration_records(
        qubit_id,
        calibration_version DESC
    );

-- ------------------------------------------------------------
-- 10. APPROVAL WORKFLOW
-- ------------------------------------------------------------

CREATE TABLE calibration_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    calibration_id BIGINT NOT NULL
        REFERENCES calibration_records(calibration_id),
    reviewer_id BIGINT NOT NULL
        REFERENCES control_users(user_id),
    decision approval_status NOT NULL,
    comments TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (calibration_id, reviewer_id)
);

-- ------------------------------------------------------------
-- 11. PULSE EXECUTION LOG
-- ------------------------------------------------------------

CREATE TABLE pulse_executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sequence_id BIGINT NOT NULL
        REFERENCES pulse_sequences(sequence_id),
    calibration_id BIGINT NOT NULL
        REFERENCES calibration_records(calibration_id),
    operator_id BIGINT NOT NULL
        REFERENCES control_users(user_id),
    execution_status execution_status NOT NULL DEFAULT 'QUEUED',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    CHECK (
        completed_at IS NULL OR
        started_at IS NOT NULL AND completed_at >= started_at
    )
);

CREATE INDEX idx_execution_status
    ON pulse_executions(execution_status, submitted_at DESC);

-- ------------------------------------------------------------
-- 12. AUDIT EVENTS
-- ------------------------------------------------------------

CREATE TABLE control_audit_log (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    action VARCHAR(80) NOT NULL,
    actor_id BIGINT REFERENCES control_users(user_id),
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity
    ON control_audit_log(entity_type, entity_id, created_at DESC);

-- ------------------------------------------------------------
-- 13. HARDWARE SAFETY VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_pulse_hardware()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    config RECORD;
BEGIN
    SELECT * INTO config
    FROM hardware_configs
    WHERE enabled = TRUE
    ORDER BY hardware_config_id
    LIMIT 1;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No enabled hardware configuration exists.';
    END IF;

    IF NEW.amplitude > config.max_amplitude THEN
        RAISE EXCEPTION 'Pulse amplitude exceeds hardware limit.';
    END IF;

    IF NEW.duration_us < config.min_duration_us
       OR NEW.duration_us > config.max_duration_us THEN
        RAISE EXCEPTION 'Pulse duration violates hardware limits.';
    END IF;

    IF abs(NEW.detuning_mhz) > config.max_detuning_mhz THEN
        RAISE EXCEPTION 'Pulse detuning exceeds hardware limits.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pulse
BEFORE INSERT OR UPDATE ON pulses
FOR EACH ROW
EXECUTE FUNCTION validate_pulse_hardware();

-- ------------------------------------------------------------
-- 14. PREVENT OVERLAPPING SEQUENCE PULSES
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_sequence_overlap()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_end NUMERIC(14,8);
BEGIN
    SELECT NEW.start_time_us + p.duration_us
    INTO new_end
    FROM pulses p
    WHERE p.pulse_id = NEW.pulse_id;

    IF new_end IS NULL THEN
        RAISE EXCEPTION 'Referenced pulse does not exist.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM sequence_steps ss
        JOIN pulses p ON p.pulse_id = ss.pulse_id
        WHERE ss.sequence_id = NEW.sequence_id
          AND ss.sequence_step_id <> COALESCE(
              NEW.sequence_step_id, -1
          )
          AND NEW.start_time_us < ss.start_time_us + p.duration_us
          AND ss.start_time_us < new_end
    ) THEN
        RAISE EXCEPTION 'Pulse sequence contains overlapping pulses.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sequence_overlap
BEFORE INSERT OR UPDATE ON sequence_steps
FOR EACH ROW
EXECUTE FUNCTION validate_sequence_overlap();

-- ------------------------------------------------------------
-- 15. CALIBRATION STATUS VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_calibration_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_state experiment_status;
    associated_qubit BIGINT;
BEGIN
    SELECT experiment_status, qubit_id
    INTO experiment_state, associated_qubit
    FROM calibration_experiments
    WHERE experiment_id = NEW.experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Calibration experiment not found.';
    END IF;

    IF experiment_state <> 'COMPLETED' THEN
        RAISE EXCEPTION
            'Calibration requires a completed experiment.';
    END IF;

    IF associated_qubit <> NEW.qubit_id THEN
        RAISE EXCEPTION
            'Calibration and experiment qubits do not match.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_calibration_validation
BEFORE INSERT OR UPDATE ON calibration_records
FOR EACH ROW
EXECUTE FUNCTION validate_calibration_decision();

-- ------------------------------------------------------------
-- 16. APPROVAL VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_calibration_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    reviewer_role VARCHAR(30);
    reviewer_active BOOLEAN;
    calibration_state calibration_status;
BEGIN
    SELECT role_name, active
    INTO reviewer_role, reviewer_active
    FROM control_users
    WHERE user_id = NEW.reviewer_id;

    IF NOT FOUND OR NOT reviewer_active THEN
        RAISE EXCEPTION 'Reviewer is not active.';
    END IF;

    IF reviewer_role NOT IN ('REVIEWER', 'ADMINISTRATOR') THEN
        RAISE EXCEPTION 'User is not authorized to approve calibration.';
    END IF;

    SELECT calibration_status
    INTO calibration_state
    FROM calibration_records
    WHERE calibration_id = NEW.calibration_id;

    IF calibration_state <> 'PENDING' THEN
        RAISE EXCEPTION 'Calibration is not awaiting approval.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_approval_validation
BEFORE INSERT OR UPDATE ON calibration_approvals
FOR EACH ROW
EXECUTE FUNCTION validate_calibration_approval();

-- ------------------------------------------------------------
-- 17. AUTOMATIC CALIBRATION APPROVAL DECISION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION evaluate_calibration_approval()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    approved_count INTEGER;
    rejected_count INTEGER;
    required_count INTEGER := 1;
BEGIN
    SELECT
        COUNT(*) FILTER (WHERE decision = 'APPROVED'),
        COUNT(*) FILTER (WHERE decision = 'REJECTED')
    INTO approved_count, rejected_count
    FROM calibration_approvals
    WHERE calibration_id = NEW.calibration_id;

    IF rejected_count > 0 THEN
        UPDATE calibration_records
        SET calibration_status = 'REVOKED'
        WHERE calibration_id = NEW.calibration_id;
    ELSIF approved_count >= required_count THEN
        UPDATE calibration_records
        SET calibration_status =
            CASE
                WHEN excitation_error <= 1 - fidelity_threshold
                    THEN 'PASSED'::calibration_status
                ELSE 'FAILED'::calibration_status
            END
        WHERE calibration_id = NEW.calibration_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_evaluate_approval
AFTER INSERT ON calibration_approvals
FOR EACH ROW
EXECUTE FUNCTION evaluate_calibration_approval();

-- ------------------------------------------------------------
-- 18. EXPERIMENT LIFECYCLE
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.experiment_status = 'COMPLETED'
       AND NEW.experiment_status <> 'COMPLETED' THEN
        RAISE EXCEPTION 'Completed experiments are immutable.';
    END IF;

    IF OLD.experiment_status IN ('FAILED', 'CANCELLED')
       AND NEW.experiment_status NOT IN ('FAILED', 'CANCELLED') THEN
        RAISE EXCEPTION 'Terminal experiment cannot be restarted.';
    END IF;

    IF NEW.experiment_status = 'RUNNING'
       AND OLD.experiment_status <> 'CREATED' THEN
        RAISE EXCEPTION 'Invalid transition to RUNNING.';
    END IF;

    IF NEW.experiment_status = 'COMPLETED'
       AND OLD.experiment_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only running experiments can complete.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF experiment_status ON calibration_experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();

-- ------------------------------------------------------------
-- 19. CONTROL VIEWS
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_latest_calibrations AS
SELECT DISTINCT ON (cr.qubit_id)
    cr.calibration_id,
    q.external_id,
    cr.calibration_version,
    cr.pi_amplitude,
    cr.pi_over_two_amplitude,
    cr.excitation_error,
    cr.calibration_status,
    cr.created_at
FROM calibration_records cr
JOIN qubits q ON q.qubit_id = cr.qubit_id
ORDER BY
    cr.qubit_id,
    cr.calibration_version DESC;

CREATE OR REPLACE VIEW v_experiment_summary AS
SELECT
    e.experiment_id,
    q.external_id,
    e.experiment_kind,
    e.experiment_status,
    COUNT(m.measurement_id) AS measurement_count,
    AVG(m.measured_probability) AS average_probability,
    MIN(m.measured_probability) AS minimum_probability,
    MAX(m.measured_probability) AS maximum_probability
FROM calibration_experiments e
JOIN qubits q ON q.qubit_id = e.qubit_id
LEFT JOIN experiment_measurements m
    ON m.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    q.external_id,
    e.experiment_kind,
    e.experiment_status;

CREATE OR REPLACE VIEW v_execution_monitor AS
SELECT
    pe.execution_id,
    ps.sequence_name,
    q.external_id,
    cu.username AS operator,
    pe.execution_status,
    pe.submitted_at,
    pe.started_at,
    pe.completed_at,
    pe.error_message
FROM pulse_executions pe
JOIN pulse_sequences ps ON ps.sequence_id = pe.sequence_id
JOIN qubits q ON q.qubit_id = ps.qubit_id
JOIN control_users cu ON cu.user_id = pe.operator_id;

-- ------------------------------------------------------------
-- 20. CALIBRATION ELIGIBILITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_calibration_eligible(
    requested_calibration_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    record calibration_records%ROWTYPE;
BEGIN
    SELECT *
    INTO record
    FROM calibration_records
    WHERE calibration_id = requested_calibration_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF record.calibration_status <> 'PASSED' THEN
        RETURN FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM qubits q
        WHERE q.qubit_id = record.qubit_id
          AND q.status = 'AVAILABLE'
    ) THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

-- ------------------------------------------------------------
-- 21. CONTROL WORKFLOW PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_experiment(
    requested_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_state experiment_status;
    qubit_state qubit_status;
BEGIN
    SELECT e.experiment_status, q.status
    INTO current_state, qubit_state
    FROM calibration_experiments e
    JOIN qubits q ON q.qubit_id = e.qubit_id
    WHERE e.experiment_id = requested_experiment_id
    FOR UPDATE OF e;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF current_state <> 'CREATED' THEN
        RAISE EXCEPTION 'Experiment is not ready to start.';
    END IF;

    IF qubit_state <> 'AVAILABLE' THEN
        RAISE EXCEPTION 'Qubit is unavailable.';
    END IF;

    UPDATE calibration_experiments
    SET experiment_status = 'RUNNING',
        started_at = NOW()
    WHERE experiment_id = requested_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- 22. SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO control_users(username, role_name)
VALUES
    ('control_operator', 'OPERATOR'),
    ('calibration_engineer', 'CALIBRATION_ENGINEER'),
    ('calibration_reviewer', 'REVIEWER'),
    ('system_admin', 'ADMINISTRATOR');

INSERT INTO qubits(
    external_id, frequency_ghz, t1_us, t2_us
)
VALUES
    ('QUBIT-001', 5.000000, 100, 80),
    ('QUBIT-002', 5.150000, 90, 70),
    ('QUBIT-003', 4.950000, 120, 95);

INSERT INTO hardware_configs(
    config_name,
    max_amplitude,
    min_duration_us,
    max_duration_us,
    max_detuning_mhz,
    max_pulses
)
VALUES (
    'STANDARD_CONTROL_CHANNEL',
    10.0,
    0.001,
    100.0,
    5.0,
    1000
);

INSERT INTO pulses(
    pulse_name,
    pulse_kind,
    amplitude,
    duration_us,
    phase_rad,
    detuning_mhz,
    created_by
)
VALUES
    (
        'X_PI',
        'X',
        3.14159265,
        1.0,
        0,
        0,
        2
    ),
    (
        'X_PI_2',
        'X',
        1.57079633,
        1.0,
        0,
        0,
        2
    ),
    (
        'Y_PI',
        'Y',
        3.14159265,
        1.0,
        1.57079633,
        0,
        2
    );

INSERT INTO pulse_sequences(
    sequence_name,
    qubit_id,
    created_by,
    sequence_version
)
VALUES
    ('RABI_CONTROL_SEQUENCE', 1, 2, 1),
    ('RAMSEY_CONTROL_SEQUENCE', 1, 2, 1);

INSERT INTO sequence_steps(
    sequence_id,
    pulse_id,
    step_number,
    start_time_us
)
VALUES
    (1, 1, 1, 0),
    (2, 2, 1, 0),
    (2, 2, 2, 2);

INSERT INTO calibration_experiments(
    qubit_id,
    hardware_config_id,
    experiment_kind,
    pulse_duration_us,
    target_amplitude,
    sample_count,
    created_by
)
VALUES
    (1, 1, 'RABI', 1.0, 3.14159265, 101, 2),
    (2, 1, 'RAMSEY', 1.0, 3.0, 101, 2),
    (3, 1, 'RABI', 1.0, 3.14159265, 101, 2);

-- Start experiments through the controlled procedure.
CALL start_experiment(1);
CALL start_experiment(2);
CALL start_experiment(3);

UPDATE calibration_experiments
SET experiment_status = 'COMPLETED',
    completed_at = NOW()
WHERE experiment_id IN (1, 2, 3);

INSERT INTO experiment_measurements(
    experiment_id,
    sample_number,
    amplitude,
    delay_us,
    measured_probability,
    measurement_count
)
VALUES
    (1, 1, 1.0, 0, 0.229848, 1000),
    (1, 2, 2.0, 0, 0.708073, 1000),
    (1, 3, 3.0, 0, 0.994996, 1000),
    (1, 4, 3.14159265, 0, 1.000000, 1000),
    (1, 5, 4.0, 0, 0.826822, 1000),
    (2, 1, 3.0, 0.5, 0.700000, 1000),
    (2, 2, 3.0, 1.0, 0.400000, 1000),
    (2, 3, 3.0, 1.5, 0.300000, 1000),
    (3, 1, 1.0, 0, 0.229848, 1000),
    (3, 2, 2.0, 0, 0.708073, 1000),
    (3, 3, 3.0, 0, 0.994996, 1000);

INSERT INTO calibration_records(
    qubit_id,
    experiment_id,
    calibration_version,
    pi_amplitude,
    pi_over_two_amplitude,
    excitation_error,
    fidelity_threshold,
    calibration_status
)
VALUES
    (1, 1, 1, 3.14159265, 1.570796325, 0.000000, 0.95, 'PENDING'),
    (3, 3, 1, 3.14159265, 1.570796325, 0.010000, 0.95, 'PENDING');

-- Approval triggers evaluate calibration quality.
INSERT INTO calibration_approvals(
    calibration_id,
    reviewer_id,
    decision,
    comments
)
VALUES
    (1, 3, 'APPROVED', 'Rabi calibration passed fidelity threshold.'),
    (2, 3, 'APPROVED', 'Calibration measurement requires further review.');

-- ------------------------------------------------------------
-- 23. EXECUTION ELIGIBILITY AND EXECUTION
-- ------------------------------------------------------------

INSERT INTO pulse_executions(
    sequence_id,
    calibration_id,
    operator_id,
    execution_status
)
SELECT
    1,
    1,
    1,
    'QUEUED'
WHERE is_calibration_eligible(1);

-- ------------------------------------------------------------
-- 24. RETRIEVAL QUERIES
-- ------------------------------------------------------------

SELECT * FROM v_latest_calibrations;

SELECT * FROM v_experiment_summary
ORDER BY experiment_id;

SELECT * FROM v_execution_monitor;

-- ------------------------------------------------------------
-- 25. RABI AGGREGATION
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    q.external_id,
    ROUND(AVG(m.measured_probability), 6) AS mean_probability,
    ROUND(MAX(m.measured_probability), 6) AS maximum_probability,
    ROUND(STDDEV_SAMP(m.measured_probability), 6) AS variation,
    COUNT(*) AS samples
FROM calibration_experiments e
JOIN qubits q ON q.qubit_id = e.qubit_id
JOIN experiment_measurements m
    ON m.experiment_id = e.experiment_id
WHERE e.experiment_kind = 'RABI'
GROUP BY e.experiment_id, q.external_id;

-- ------------------------------------------------------------
-- 26. CALIBRATION ELIGIBILITY REPORT
-- ------------------------------------------------------------

SELECT
    cr.calibration_id,
    q.external_id,
    cr.calibration_version,
    cr.calibration_status,
    is_calibration_eligible(cr.calibration_id) AS eligible_for_execution
FROM calibration_records cr
JOIN qubits q ON q.qubit_id = cr.qubit_id;

-- ------------------------------------------------------------
-- 27. WINDOW FUNCTION: CALIBRATION VERSION HISTORY
-- ------------------------------------------------------------

SELECT
    q.external_id,
    cr.calibration_version,
    cr.pi_amplitude,
    cr.excitation_error,
    cr.calibration_status,
    LAG(cr.pi_amplitude) OVER (
        PARTITION BY cr.qubit_id
        ORDER BY cr.calibration_version
    ) AS previous_pi_amplitude
FROM calibration_records cr
JOIN qubits q ON q.qubit_id = cr.qubit_id
ORDER BY q.external_id, cr.calibration_version;

-- ------------------------------------------------------------
-- 28. CTE: BEST RABI MEASUREMENT
-- ------------------------------------------------------------

WITH ranked_measurements AS (
    SELECT
        experiment_id,
        sample_number,
        amplitude,
        measured_probability,
        ROW_NUMBER() OVER (
            PARTITION BY experiment_id
            ORDER BY measured_probability DESC, sample_number
        ) AS ranking
    FROM experiment_measurements
)
SELECT
    experiment_id,
    sample_number,
    amplitude AS candidate_pi_amplitude,
    measured_probability
FROM ranked_measurements
WHERE ranking = 1;

-- ------------------------------------------------------------
-- 29. TRANSACTIONAL EXECUTION EXAMPLE
-- ------------------------------------------------------------

COMMIT;

-- Example of an independently executable transaction:
--
-- BEGIN;
-- SELECT * FROM calibration_records
-- WHERE calibration_id = 1 FOR UPDATE;
--
-- SELECT is_calibration_eligible(1);
--
-- INSERT INTO pulse_executions(
--     sequence_id,
--     calibration_id,
--     operator_id,
--     execution_status
-- )
-- SELECT 1, 1, 1, 'QUEUED'
-- WHERE is_calibration_eligible(1);
--
-- COMMIT;
--
-- If validation fails, issue ROLLBACK.

-- ------------------------------------------------------------
-- 30. OPERATIONAL FAILURE INVESTIGATION
-- ------------------------------------------------------------

SELECT
    experiment_id,
    experiment_status,
    failure_reason,
    started_at,
    completed_at
FROM calibration_experiments
WHERE experiment_status IN ('FAILED', 'CANCELLED');

SELECT
    audit_id,
    entity_type,
    entity_id,
    action,
    details,
    created_at
FROM control_audit_log
ORDER BY created_at DESC
LIMIT 50;

-- ------------------------------------------------------------
-- END OF QUANTUM CONTROL DATABASE
-- ------------------------------------------------------------
