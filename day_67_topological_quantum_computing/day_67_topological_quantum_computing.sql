/*
 * Majorana-Based Topological Quantum Computing
 * PostgreSQL 15+
 *
 * Relational experimental workflow:
 * Research projects
 *   -> Devices
 *   -> Majorana zero modes
 *   -> Fusion configurations
 *   -> Experimental conditions
 *   -> Braid sequences
 *   -> Parity measurements
 *   -> Validation
 *   -> Experiment results
 *
 * This database records mathematical simulations and experimental
 * metadata. Passing database validation does not establish that a
 * physical device hosts genuine Majorana zero modes.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS majorana_lab;

SET search_path TO majorana_lab, public;

CREATE TYPE fusion_channel AS ENUM (
    'VACUUM',
    'FERMION'
);

CREATE TYPE device_status AS ENUM (
    'DESIGN',
    'CALIBRATION',
    'READY',
    'MAINTENANCE',
    'RETIRED'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATING',
    'REJECTED',
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE braid_orientation AS ENUM (
    'CLOCKWISE',
    'COUNTERCLOCKWISE'
);

CREATE TYPE measurement_type AS ENUM (
    'PARITY',
    'ENERGY_GAP',
    'COHERENCE',
    'TEMPERATURE'
);

-- Research projects organize device and experiment ownership.
CREATE TABLE research_projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(150) NOT NULL,
    principal_investigator VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (length(trim(project_code)) > 0),
    CHECK (length(trim(project_name)) > 0)
);

CREATE TABLE quantum_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES research_projects(project_id),
    device_code VARCHAR(50) NOT NULL UNIQUE,
    architecture VARCHAR(100) NOT NULL,
    majorana_mode_count INTEGER NOT NULL,
    minimum_energy_gap NUMERIC(14,8) NOT NULL,
    status device_status NOT NULL DEFAULT 'DESIGN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (majorana_mode_count >= 4),
    CHECK (majorana_mode_count % 2 = 0),
    CHECK (minimum_energy_gap > 0)
);

-- Each zero mode has a device-local index.
CREATE TABLE majorana_modes (
    mode_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES quantum_devices(device_id),
    mode_index INTEGER NOT NULL,
    location_description VARCHAR(200) NOT NULL,
    localization_quality NUMERIC(6,5),
    CHECK (mode_index >= 1),
    CHECK (
        localization_quality IS NULL OR
        localization_quality BETWEEN 0 AND 1
    ),
    UNIQUE (device_id, mode_index)
);

CREATE TABLE fusion_configurations (
    fusion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES quantum_devices(device_id),
    first_mode_id BIGINT NOT NULL REFERENCES majorana_modes(mode_id),
    second_mode_id BIGINT NOT NULL REFERENCES majorana_modes(mode_id),
    channel fusion_channel NOT NULL,
    occupation INTEGER NOT NULL,
    total_parity SMALLINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (first_mode_id <> second_mode_id),
    CHECK (occupation IN (0, 1)),
    CHECK (total_parity IN (-1, 1)),
    CHECK (
        (occupation = 0 AND channel = 'VACUUM' AND total_parity = 1)
        OR
        (occupation = 1 AND channel = 'FERMION' AND total_parity = -1)
    )
);

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES research_projects(project_id),
    device_id BIGINT NOT NULL REFERENCES quantum_devices(device_id),
    experiment_code VARCHAR(60) NOT NULL UNIQUE,
    status experiment_status NOT NULL DEFAULT 'CREATED',
    energy_gap NUMERIC(14,8) NOT NULL,
    temperature NUMERIC(14,8) NOT NULL,
    coherence_time NUMERIC(16,8) NOT NULL,
    operation_time NUMERIC(16,8) NOT NULL,
    parity_measurement_error NUMERIC(8,7) NOT NULL,
    initial_parity SMALLINT NOT NULL,
    final_parity SMALLINT,
    initial_state JSONB NOT NULL DEFAULT
        '{"amplitudes":[0.7071067812,0.7071067812]}'::jsonb,
    final_state JSONB,
    fidelity NUMERIC(12,10),
    failure_reason TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CHECK (energy_gap >= 0),
    CHECK (temperature >= 0),
    CHECK (coherence_time > 0),
    CHECK (operation_time > 0),
    CHECK (parity_measurement_error BETWEEN 0 AND 1),
    CHECK (initial_parity IN (-1, 1)),
    CHECK (final_parity IS NULL OR final_parity IN (-1, 1)),
    CHECK (fidelity IS NULL OR fidelity BETWEEN 0 AND 1),
    CHECK (jsonb_typeof(initial_state) = 'object'),
    CHECK (
        final_state IS NULL OR
        jsonb_typeof(final_state) = 'object'
    )
);

CREATE TABLE braid_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    operation_number INTEGER NOT NULL,
    generator_index SMALLINT NOT NULL,
    orientation braid_orientation NOT NULL,
    left_mode_id BIGINT NOT NULL REFERENCES majorana_modes(mode_id),
    right_mode_id BIGINT NOT NULL REFERENCES majorana_modes(mode_id),
    executed_at TIMESTAMPTZ,
    CHECK (operation_number >= 1),
    CHECK (generator_index IN (1, 2)),
    CHECK (left_mode_id <> right_mode_id),
    UNIQUE (experiment_id, operation_number)
);

CREATE TABLE parity_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    measurement_sequence INTEGER NOT NULL,
    measurement_kind measurement_type NOT NULL,
    measured_value NUMERIC(16,8) NOT NULL,
    expected_value NUMERIC(16,8),
    measurement_error NUMERIC(8,7),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (measurement_sequence >= 1),
    CHECK (
        measurement_error IS NULL OR
        measurement_error BETWEEN 0 AND 1
    ),
    UNIQUE (experiment_id, measurement_sequence)
);

CREATE TABLE experiment_policy (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL UNIQUE,
    minimum_energy_gap NUMERIC(14,8) NOT NULL,
    maximum_measurement_error NUMERIC(8,7) NOT NULL,
    maximum_operation_time NUMERIC(16,8) NOT NULL,
    require_ready_device BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (minimum_energy_gap > 0),
    CHECK (maximum_measurement_error BETWEEN 0 AND 1),
    CHECK (maximum_operation_time > 0)
);

CREATE TABLE validation_results (
    validation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    policy_id BIGINT NOT NULL REFERENCES experiment_policy(policy_id),
    passed BOOLEAN NOT NULL,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(findings) = 'array')
);

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id),
    event_type VARCHAR(40) NOT NULL,
    event_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(event_details) = 'object')
);

-- Query-oriented indexes.
CREATE INDEX idx_devices_project_status
    ON quantum_devices(project_id, status);

CREATE INDEX idx_modes_device
    ON majorana_modes(device_id, mode_index);

CREATE INDEX idx_experiments_project_started
    ON experiments(project_id, started_at DESC);

CREATE INDEX idx_experiments_status
    ON experiments(status, started_at DESC);

CREATE INDEX idx_braids_experiment_sequence
    ON braid_operations(experiment_id, operation_number);

CREATE INDEX idx_measurements_experiment_type
    ON parity_measurements(experiment_id, measurement_kind);

CREATE INDEX idx_audit_experiment_time
    ON experiment_audit(experiment_id, event_time DESC);

CREATE INDEX idx_validation_findings
    ON validation_results USING GIN(findings);

-- Prevent experiments from referencing devices belonging to another project.
CREATE OR REPLACE FUNCTION validate_experiment_device()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM quantum_devices d
        WHERE d.device_id = NEW.device_id
          AND d.project_id = NEW.project_id
    ) THEN
        RAISE EXCEPTION
            'Experiment device must belong to its research project.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_device
BEFORE INSERT OR UPDATE OF device_id, project_id
ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_device();

-- Ensure braid operations use two modes from the same device.
CREATE OR REPLACE FUNCTION validate_braid_modes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_device BIGINT;
    left_device BIGINT;
    right_device BIGINT;
    left_index INTEGER;
    right_index INTEGER;
BEGIN
    SELECT device_id
    INTO experiment_device
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    SELECT device_id, mode_index
    INTO left_device, left_index
    FROM majorana_modes
    WHERE mode_id = NEW.left_mode_id;

    SELECT device_id, mode_index
    INTO right_device, right_index
    FROM majorana_modes
    WHERE mode_id = NEW.right_mode_id;

    IF left_device IS DISTINCT FROM experiment_device
       OR right_device IS DISTINCT FROM experiment_device THEN
        RAISE EXCEPTION
            'Braid modes must belong to the experiment device.';
    END IF;

    IF abs(left_index - right_index) <> 1 THEN
        RAISE EXCEPTION
            'A braid generator must exchange adjacent modes.';
    END IF;

    IF left_index <> NEW.generator_index
       OR right_index <> NEW.generator_index + 1 THEN
        RAISE EXCEPTION
            'Mode indices do not match the braid generator.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_braid_modes
BEFORE INSERT OR UPDATE
ON braid_operations
FOR EACH ROW
EXECUTE FUNCTION validate_braid_modes();

-- Audit experiment state transitions.
CREATE OR REPLACE FUNCTION audit_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO experiment_audit (
            experiment_id,
            event_type,
            event_details
        )
        VALUES (
            NEW.experiment_id,
            'CREATED',
            jsonb_build_object('status', NEW.status)
        );

        RETURN NEW;
    END IF;

    IF NEW.status IS DISTINCT FROM OLD.status THEN
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

CREATE TRIGGER trg_audit_experiment_status
AFTER INSERT OR UPDATE OF status
ON experiments
FOR EACH ROW
EXECUTE FUNCTION audit_experiment_status();

-- Centralized policy evaluation.
CREATE OR REPLACE FUNCTION evaluate_experiment(
    p_experiment_id BIGINT,
    p_policy_id BIGINT
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    e experiments%ROWTYPE;
    p experiment_policy%ROWTYPE;
    d quantum_devices%ROWTYPE;
    findings JSONB := '[]'::jsonb;
    braid_count INTEGER;
BEGIN
    SELECT *
    INTO e
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found: %', p_experiment_id;
    END IF;

    SELECT *
    INTO p
    FROM experiment_policy
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active policy not found: %', p_policy_id;
    END IF;

    SELECT *
    INTO d
    FROM quantum_devices
    WHERE device_id = e.device_id;

    IF e.energy_gap < p.minimum_energy_gap THEN
        findings := findings ||
            jsonb_build_array('ENERGY_GAP_BELOW_THRESHOLD');
    END IF;

    IF e.parity_measurement_error > p.maximum_measurement_error THEN
        findings := findings ||
            jsonb_build_array('PARITY_ERROR_TOO_HIGH');
    END IF;

    IF e.operation_time > p.maximum_operation_time THEN
        findings := findings ||
            jsonb_build_array('OPERATION_TIME_EXCEEDED');
    END IF;

    IF e.operation_time >= e.coherence_time THEN
        findings := findings ||
            jsonb_build_array('COHERENCE_WINDOW_EXCEEDED');
    END IF;

    IF e.temperature > e.energy_gap THEN
        findings := findings ||
            jsonb_build_array('TEMPERATURE_EXCEEDS_GAP_SCALE');
    END IF;

    IF p.require_ready_device AND d.status <> 'READY' THEN
        findings := findings ||
            jsonb_build_array('DEVICE_NOT_READY');
    END IF;

    SELECT count(*)
    INTO braid_count
    FROM braid_operations
    WHERE experiment_id = p_experiment_id;

    IF braid_count = 0 THEN
        findings := findings ||
            jsonb_build_array('NO_BRAID_OPERATIONS');
    END IF;

    RETURN jsonb_build_object(
        'passed',
        jsonb_array_length(findings) = 0,
        'findings',
        findings,
        'braid_count',
        braid_count
    );
END;
$$;

-- Transactional workflow: validate and determine eligibility.
CREATE OR REPLACE PROCEDURE process_experiment(
    p_experiment_id BIGINT,
    p_policy_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    evaluation JSONB;
    passed BOOLEAN;
    findings JSONB;
BEGIN
    -- Serialize concurrent processing of the same experiment.
    PERFORM 1
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    UPDATE experiments
    SET status = 'VALIDATING'
    WHERE experiment_id = p_experiment_id
      AND status = 'CREATED';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Only CREATED experiments can enter validation.';
    END IF;

    evaluation := evaluate_experiment(
        p_experiment_id,
        p_policy_id
    );

    passed := (evaluation ->> 'passed')::BOOLEAN;
    findings := evaluation -> 'findings';

    INSERT INTO validation_results (
        experiment_id,
        policy_id,
        passed,
        findings
    )
    VALUES (
        p_experiment_id,
        p_policy_id,
        passed,
        findings
    );

    UPDATE experiments
    SET status = CASE
        WHEN passed THEN 'RUNNING'::experiment_status
        ELSE 'REJECTED'::experiment_status
    END,
    failure_reason = CASE
        WHEN passed THEN NULL
        ELSE findings::TEXT
    END
    WHERE experiment_id = p_experiment_id;

END;
$$;

-- Record a completed experiment with parity conservation.
CREATE OR REPLACE PROCEDURE complete_experiment(
    p_experiment_id BIGINT,
    p_final_parity SMALLINT,
    p_final_state JSONB,
    p_fidelity NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    e experiments%ROWTYPE;
BEGIN
    IF p_final_parity NOT IN (-1, 1) THEN
        RAISE EXCEPTION 'Invalid final parity.';
    END IF;

    IF p_final_state IS NULL OR
       jsonb_typeof(p_final_state) <> 'object' THEN
        RAISE EXCEPTION 'Final state must be a JSON object.';
    END IF;

    IF p_fidelity NOT BETWEEN 0 AND 1 THEN
        RAISE EXCEPTION 'Fidelity must be between zero and one.';
    END IF;

    SELECT *
    INTO e
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF e.status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only RUNNING experiments can complete.';
    END IF;

    -- Fermion parity must be conserved by ideal braiding.
    IF p_final_parity <> e.initial_parity THEN
        RAISE EXCEPTION
            'Parity conservation violation: initial %, final %.',
            e.initial_parity,
            p_final_parity;
    END IF;

    UPDATE experiments
    SET status = 'COMPLETED',
        final_parity = p_final_parity,
        final_state = p_final_state,
        fidelity = p_fidelity,
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- Reporting view for experiment governance.
CREATE VIEW experiment_governance_report AS
SELECT
    e.experiment_id,
    e.experiment_code,
    p.project_code,
    d.device_code,
    d.status AS device_status,
    e.status AS experiment_status,
    e.energy_gap,
    e.temperature,
    e.coherence_time,
    e.operation_time,
    e.parity_measurement_error,
    e.initial_parity,
    e.final_parity,
    e.fidelity,
    count(DISTINCT b.operation_id) AS braid_operations,
    count(DISTINCT m.measurement_id) AS measurements,
    bool_and(v.passed) AS all_validations_passed
FROM experiments e
JOIN research_projects p
    ON p.project_id = e.project_id
JOIN quantum_devices d
    ON d.device_id = e.device_id
LEFT JOIN braid_operations b
    ON b.experiment_id = e.experiment_id
LEFT JOIN parity_measurements m
    ON m.experiment_id = e.experiment_id
LEFT JOIN validation_results v
    ON v.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_code,
    p.project_code,
    d.device_code,
    d.status,
    e.status,
    e.energy_gap,
    e.temperature,
    e.coherence_time,
    e.operation_time,
    e.parity_measurement_error,
    e.initial_parity,
    e.final_parity,
    e.fidelity;

-- Sample research project.
INSERT INTO research_projects (
    project_code,
    project_name,
    principal_investigator
)
VALUES (
    'MAJ-RESEARCH-001',
    'Majorana Zero Mode Braid Validation',
    'Dr. Research Lead'
);

-- Four-mode device.
INSERT INTO quantum_devices (
    project_id,
    device_code,
    architecture,
    majorana_mode_count,
    minimum_energy_gap,
    status
)
SELECT
    project_id,
    'DEVICE-MZM-001',
    'Semiconductor-superconductor nanowire network',
    4,
    0.1,
    'READY'
FROM research_projects
WHERE project_code = 'MAJ-RESEARCH-001';

INSERT INTO majorana_modes (
    device_id,
    mode_index,
    location_description,
    localization_quality
)
SELECT
    d.device_id,
    x.mode_index,
    x.description,
    x.quality
FROM quantum_devices d
CROSS JOIN (
    VALUES
        (1, 'Left wire endpoint', 0.98),
        (2, 'Central junction endpoint', 0.96),
        (3, 'Right junction endpoint', 0.97),
        (4, 'Outer wire endpoint', 0.95)
) AS x(mode_index, description, quality)
WHERE d.device_code = 'DEVICE-MZM-001';

-- Two possible fusion outcomes.
INSERT INTO fusion_configurations (
    device_id,
    first_mode_id,
    second_mode_id,
    channel,
    occupation,
    total_parity
)
SELECT
    d.device_id,
    m1.mode_id,
    m2.mode_id,
    'VACUUM',
    0,
    1
FROM quantum_devices d
JOIN majorana_modes m1
    ON m1.device_id = d.device_id AND m1.mode_index = 1
JOIN majorana_modes m2
    ON m2.device_id = d.device_id AND m2.mode_index = 2
WHERE d.device_code = 'DEVICE-MZM-001';

INSERT INTO fusion_configurations (
    device_id,
    first_mode_id,
    second_mode_id,
    channel,
    occupation,
    total_parity
)
SELECT
    d.device_id,
    m1.mode_id,
    m2.mode_id,
    'FERMION',
    1,
    -1
FROM quantum_devices d
JOIN majorana_modes m1
    ON m1.device_id = d.device_id AND m1.mode_index = 3
JOIN majorana_modes m2
    ON m2.device_id = d.device_id AND m2.mode_index = 4
WHERE d.device_code = 'DEVICE-MZM-001';

INSERT INTO experiment_policy (
    policy_name,
    minimum_energy_gap,
    maximum_measurement_error,
    maximum_operation_time,
    require_ready_device
)
VALUES
(
    'STRICT-MAJORANA-POLICY',
    0.1,
    0.05,
    10,
    TRUE
),
(
    'RESEARCH-DIAGNOSTIC-POLICY',
    0.02,
    0.15,
    30,
    FALSE
);

-- Valid experiment.
INSERT INTO experiments (
    project_id,
    device_id,
    experiment_code,
    energy_gap,
    temperature,
    coherence_time,
    operation_time,
    parity_measurement_error,
    initial_parity
)
SELECT
    p.project_id,
    d.device_id,
    'EXP-MAJ-001',
    0.25,
    0.01,
    100,
    2,
    0.01,
    1
FROM research_projects p
JOIN quantum_devices d
    ON d.project_id = p.project_id
WHERE p.project_code = 'MAJ-RESEARCH-001'
  AND d.device_code = 'DEVICE-MZM-001';

-- Four sequential braid operations.
INSERT INTO braid_operations (
    experiment_id,
    operation_number,
    generator_index,
    orientation,
    left_mode_id,
    right_mode_id
)
SELECT
    e.experiment_id,
    x.operation_number,
    x.generator_index,
    x.orientation::braid_orientation,
    ml.mode_id,
    mr.mode_id
FROM experiments e
CROSS JOIN (
    VALUES
        (1, 1, 'CLOCKWISE'),
        (2, 2, 'CLOCKWISE'),
        (3, 1, 'CLOCKWISE'),
        (4, 2, 'COUNTERCLOCKWISE')
) AS x(operation_number, generator_index, orientation)
JOIN majorana_modes ml
    ON ml.device_id = e.device_id
   AND ml.mode_index = x.generator_index
JOIN majorana_modes mr
    ON mr.device_id = e.device_id
   AND mr.mode_index = x.generator_index + 1
WHERE e.experiment_code = 'EXP-MAJ-001';

INSERT INTO parity_measurements (
    experiment_id,
    measurement_sequence,
    measurement_kind,
    measured_value,
    expected_value,
    measurement_error
)
SELECT
    experiment_id,
    1,
    'PARITY',
    1,
    1,
    0.01
FROM experiments
WHERE experiment_code = 'EXP-MAJ-001';

-- Invalid operating conditions: insufficient gap and long operation.
INSERT INTO experiments (
    project_id,
    device_id,
    experiment_code,
    energy_gap,
    temperature,
    coherence_time,
    operation_time,
    parity_measurement_error,
    initial_parity
)
SELECT
    p.project_id,
    d.device_id,
    'EXP-MAJ-002',
    0.01,
    0.02,
    10,
    20,
    0.12,
    1
FROM research_projects p
JOIN quantum_devices d
    ON d.project_id = p.project_id
WHERE p.project_code = 'MAJ-RESEARCH-001'
  AND d.device_code = 'DEVICE-MZM-001';

INSERT INTO braid_operations (
    experiment_id,
    operation_number,
    generator_index,
    orientation,
    left_mode_id,
    right_mode_id
)
SELECT
    e.experiment_id,
    1,
    1,
    'CLOCKWISE',
    ml.mode_id,
    mr.mode_id
FROM experiments e
JOIN majorana_modes ml
    ON ml.device_id = e.device_id AND ml.mode_index = 1
JOIN majorana_modes mr
    ON mr.device_id = e.device_id AND mr.mode_index = 2
WHERE e.experiment_code = 'EXP-MAJ-002';

-- Transactional validation of both experiments.
CALL process_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_code = 'EXP-MAJ-001'
    ),
    (
        SELECT policy_id
        FROM experiment_policy
        WHERE policy_name = 'STRICT-MAJORANA-POLICY'
    )
);

CALL process_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_code = 'EXP-MAJ-002'
    ),
    (
        SELECT policy_id
        FROM experiment_policy
        WHERE policy_name = 'STRICT-MAJORANA-POLICY'
    )
);

-- Complete the valid experiment with parity conserved.
CALL complete_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_code = 'EXP-MAJ-001'
    ),
    1,
    '{"amplitudes":[0.7071067812,0.7071067812]}'::jsonb,
    1.0
);

-- Retrieve experiments and their governance decisions.
SELECT *
FROM experiment_governance_report
ORDER BY experiment_id;

-- Retrieve individual braid histories.
SELECT
    e.experiment_code,
    b.operation_number,
    b.generator_index,
    b.orientation,
    ml.mode_index AS first_mode,
    mr.mode_index AS second_mode,
    b.executed_at
FROM braid_operations b
JOIN experiments e
    ON e.experiment_id = b.experiment_id
JOIN majorana_modes ml
    ON ml.mode_id = b.left_mode_id
JOIN majorana_modes mr
    ON mr.mode_id = b.right_mode_id
ORDER BY e.experiment_id, b.operation_number;

-- Aggregate validation outcomes.
SELECT
    p.policy_name,
    count(*) AS total_validations,
    count(*) FILTER (WHERE v.passed) AS passed,
    count(*) FILTER (WHERE NOT v.passed) AS rejected
FROM validation_results v
JOIN experiment_policy p
    ON p.policy_id = v.policy_id
GROUP BY p.policy_name;

-- Identify parity violations in completed experiments.
SELECT
    experiment_code,
    initial_parity,
    final_parity,
    status
FROM experiments
WHERE status = 'COMPLETED'
  AND initial_parity <> final_parity;

-- Inspect rejection findings.
SELECT
    e.experiment_code,
    v.findings
FROM validation_results v
JOIN experiments e
    ON e.experiment_id = v.experiment_id
WHERE NOT v.passed;

-- Inspect the chronological audit trail.
SELECT
    e.experiment_code,
    a.event_type,
    a.event_details,
    a.event_time
FROM experiment_audit a
JOIN experiments e
    ON e.experiment_id = a.experiment_id
ORDER BY a.event_time, a.audit_id;

-- CTE-based experiment acceptance statistics.
WITH experiment_statistics AS (
    SELECT
        status,
        count(*) AS experiment_count,
        avg(fidelity) AS average_fidelity
    FROM experiments
    GROUP BY status
)
SELECT
    status,
    experiment_count,
    round(average_fidelity, 6) AS average_fidelity
FROM experiment_statistics
ORDER BY status;

COMMIT;
