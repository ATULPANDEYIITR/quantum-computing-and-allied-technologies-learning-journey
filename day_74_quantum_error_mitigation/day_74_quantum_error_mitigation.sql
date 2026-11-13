/*
 * Quantum Error Mitigation relational experiment platform.
 *
 * PostgreSQL 15+
 *
 * Models:
 * - Research projects and experiment ownership.
 * - Quantum circuits and noise channels.
 * - Experimental runs and measurement results.
 * - Readout calibration records.
 * - Mitigation methods.
 * - Zero-noise extrapolation observations.
 * - Governance policies and eligibility decisions.
 * - Immutable audit history.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS qem;

SET search_path TO qem, public;

CREATE TYPE noise_type AS ENUM (
    'BIT_FLIP',
    'PHASE_FLIP',
    'DEPOLARIZING',
    'AMPLITUDE_DAMPING'
);

CREATE TYPE mitigation_method AS ENUM (
    'NONE',
    'READOUT_CALIBRATION',
    'ZERO_NOISE_EXTRAPOLATION',
    'PROBABILISTIC_ERROR_CANCELLATION'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'REJECTED'
);

CREATE TYPE eligibility_status AS ENUM (
    'ELIGIBLE',
    'INELIGIBLE',
    'PENDING'
);

CREATE TABLE research_projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code VARCHAR(40) NOT NULL UNIQUE,
    project_name VARCHAR(200) NOT NULL,
    owner_name VARCHAR(150) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    role_name VARCHAR(40) NOT NULL CHECK (
        role_name IN (
            'RESEARCHER',
            'PRINCIPAL_INVESTIGATOR',
            'REVIEWER',
            'ADMINISTRATOR'
        )
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES research_projects(project_id),
    circuit_name VARCHAR(150) NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),
    gate_count INTEGER NOT NULL CHECK (gate_count >= 0),
    circuit_depth INTEGER NOT NULL CHECK (circuit_depth >= 0),
    observable VARCHAR(100) NOT NULL,
    created_by BIGINT NOT NULL REFERENCES researchers(researcher_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, circuit_name)
);

CREATE TABLE noise_channels (
    noise_channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    noise_name VARCHAR(100) NOT NULL,
    noise_category noise_type NOT NULL,
    error_probability NUMERIC(10,8) NOT NULL CHECK (
        error_probability BETWEEN 0 AND 1
    ),
    calibration_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device_name VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE(noise_name, device_name, calibration_timestamp)
);

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_code VARCHAR(50) NOT NULL UNIQUE,
    circuit_id BIGINT NOT NULL REFERENCES quantum_circuits(circuit_id),
    noise_channel_id BIGINT NOT NULL REFERENCES noise_channels(noise_channel_id),
    created_by BIGINT NOT NULL REFERENCES researchers(researcher_id),
    status experiment_status NOT NULL DEFAULT 'CREATED',
    shots INTEGER NOT NULL CHECK (shots > 0),
    readout_error NUMERIC(10,8) NOT NULL CHECK (
        readout_error BETWEEN 0 AND 1
    ),
    ideal_expectation NUMERIC(12,9) CHECK (
        ideal_expectation BETWEEN -1 AND 1
    ),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        completed_at IS NULL OR
        started_at IS NOT NULL AND
        completed_at >= started_at
    )
);

CREATE TABLE mitigation_methods (
    method_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    method_code mitigation_method NOT NULL UNIQUE,
    method_description TEXT NOT NULL,
    requires_calibration BOOLEAN NOT NULL DEFAULT FALSE,
    resource_multiplier NUMERIC(12,4) NOT NULL CHECK (
        resource_multiplier >= 1
    )
);

CREATE TABLE calibration_records (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    noise_channel_id BIGINT NOT NULL REFERENCES noise_channels(noise_channel_id),
    experiment_id BIGINT REFERENCES experiments(experiment_id),
    error_0_to_1 NUMERIC(10,8) NOT NULL CHECK (
        error_0_to_1 BETWEEN 0 AND 1
    ),
    error_1_to_0 NUMERIC(10,8) NOT NULL CHECK (
        error_1_to_0 BETWEEN 0 AND 1
    ),
    calibration_shots INTEGER NOT NULL CHECK (calibration_shots > 0),
    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    calibrated_by BIGINT NOT NULL REFERENCES researchers(researcher_id),
    CHECK (
        ABS(1 - error_0_to_1 - error_1_to_0) > 0.00000001
    )
);

CREATE TABLE experiment_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id),
    method_id BIGINT NOT NULL REFERENCES mitigation_methods(method_id),
    estimate NUMERIC(14,10) NOT NULL CHECK (
        estimate BETWEEN -1.5 AND 1.5
    ),
    standard_error NUMERIC(14,10) NOT NULL CHECK (
        standard_error >= 0
    ),
    shot_count INTEGER NOT NULL CHECK (shot_count > 0),
    bias NUMERIC(14,10),
    resource_cost NUMERIC(16,4) NOT NULL CHECK (
        resource_cost >= 0
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(experiment_id, method_id)
);

CREATE TABLE extrapolation_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id),
    method_id BIGINT NOT NULL REFERENCES mitigation_methods(method_id),
    noise_scale NUMERIC(10,4) NOT NULL CHECK (noise_scale > 0),
    observed_expectation NUMERIC(14,10) NOT NULL CHECK (
        observed_expectation BETWEEN -1.5 AND 1.5
    ),
    shot_count INTEGER NOT NULL CHECK (shot_count > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(experiment_id, method_id, noise_scale)
);

CREATE TABLE governance_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name VARCHAR(150) NOT NULL UNIQUE,
    maximum_noise NUMERIC(10,8) NOT NULL CHECK (
        maximum_noise BETWEEN 0 AND 1
    ),
    minimum_shots INTEGER NOT NULL CHECK (minimum_shots > 0),
    maximum_standard_error NUMERIC(12,10) NOT NULL CHECK (
        maximum_standard_error > 0
    ),
    require_calibration BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE policy_allowed_methods (
    policy_id BIGINT NOT NULL REFERENCES governance_policies(policy_id)
        ON DELETE CASCADE,
    method_id BIGINT NOT NULL REFERENCES mitigation_methods(method_id),
    PRIMARY KEY(policy_id, method_id)
);

CREATE TABLE eligibility_decisions (
    decision_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id),
    result_id BIGINT NOT NULL REFERENCES experiment_results(result_id),
    policy_id BIGINT NOT NULL REFERENCES governance_policies(policy_id),
    status eligibility_status NOT NULL,
    violations JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluated_by BIGINT REFERENCES researchers(researcher_id),
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(result_id, policy_id)
);

CREATE TABLE audit_events (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entity_type VARCHAR(80) NOT NULL,
    entity_id BIGINT NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- High-value indexes for project and experiment retrieval.
CREATE INDEX idx_circuits_project
    ON quantum_circuits(project_id);

CREATE INDEX idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_creator
    ON experiments(created_by, created_at DESC);

CREATE INDEX idx_results_experiment
    ON experiment_results(experiment_id);

CREATE INDEX idx_observations_experiment_scale
    ON extrapolation_observations(experiment_id, noise_scale);

CREATE INDEX idx_decisions_status
    ON eligibility_decisions(status, evaluated_at DESC);

CREATE INDEX idx_audit_entity
    ON audit_events(entity_type, entity_id, created_at DESC);

CREATE INDEX idx_audit_data
    ON audit_events USING GIN(event_data);

INSERT INTO mitigation_methods (
    method_code,
    method_description,
    requires_calibration,
    resource_multiplier
)
VALUES
(
    'NONE',
    'Unmitigated measurement baseline',
    FALSE,
    1.0
),
(
    'READOUT_CALIBRATION',
    'Correct measurement assignment errors using a calibrated confusion matrix',
    TRUE,
    1.2
),
(
    'ZERO_NOISE_EXTRAPOLATION',
    'Extrapolate measurements toward the zero-noise limit',
    FALSE,
    3.0
),
(
    'PROBABILISTIC_ERROR_CANCELLATION',
    'Use quasi-probability sampling to estimate an inverse noisy channel',
    TRUE,
    10.0
);

INSERT INTO researchers(email, full_name, role_name)
VALUES
('researcher@example.org', 'Quantum Researcher', 'RESEARCHER'),
('principal@example.org', 'Principal Investigator', 'PRINCIPAL_INVESTIGATOR'),
('reviewer@example.org', 'Experiment Reviewer', 'REVIEWER'),
('admin@example.org', 'Platform Administrator', 'ADMINISTRATOR');

INSERT INTO research_projects(
    project_code,
    project_name,
    owner_name
)
VALUES
(
    'QEM-2026',
    'Quantum Error Mitigation Benchmark',
    'Quantum Research Group'
);

INSERT INTO quantum_circuits(
    project_id,
    circuit_name,
    qubit_count,
    gate_count,
    circuit_depth,
    observable,
    created_by
)
SELECT
    project_id,
    'single-qubit-z-measurement',
    1,
    3,
    2,
    'Pauli-Z',
    (SELECT researcher_id FROM researchers
     WHERE email = 'researcher@example.org')
FROM research_projects
WHERE project_code = 'QEM-2026';

INSERT INTO noise_channels(
    noise_name,
    noise_category,
    error_probability,
    device_name
)
VALUES
(
    'bit-flip-channel-8pct',
    'BIT_FLIP',
    0.08,
    'QPU-SIMULATOR-01'
),
(
    'depolarizing-channel-5pct',
    'DEPOLARIZING',
    0.05,
    'QPU-SIMULATOR-01'
),
(
    'phase-flip-channel-3pct',
    'PHASE_FLIP',
    0.03,
    'QPU-SIMULATOR-01'
);

INSERT INTO experiments(
    experiment_code,
    circuit_id,
    noise_channel_id,
    created_by,
    shots,
    readout_error,
    ideal_expectation
)
SELECT
    'QEM-RUN-001',
    c.circuit_id,
    n.noise_channel_id,
    r.researcher_id,
    30000,
    0.04,
    1.0
FROM quantum_circuits c
JOIN research_projects p ON p.project_id = c.project_id
JOIN noise_channels n
    ON n.noise_name = 'bit-flip-channel-8pct'
JOIN researchers r
    ON r.email = 'researcher@example.org'
WHERE p.project_code = 'QEM-2026';

INSERT INTO experiments(
    experiment_code,
    circuit_id,
    noise_channel_id,
    created_by,
    shots,
    readout_error,
    ideal_expectation,
    status
)
SELECT
    'QEM-RUN-002',
    c.circuit_id,
    n.noise_channel_id,
    r.researcher_id,
    100,
    0.04,
    1.0,
    'CREATED'
FROM quantum_circuits c
JOIN research_projects p ON p.project_id = c.project_id
JOIN noise_channels n
    ON n.noise_name = 'depolarizing-channel-5pct'
JOIN researchers r
    ON r.email = 'researcher@example.org'
WHERE p.project_code = 'QEM-2026';

INSERT INTO calibration_records(
    noise_channel_id,
    experiment_id,
    error_0_to_1,
    error_1_to_0,
    calibration_shots,
    calibrated_by
)
SELECT
    n.noise_channel_id,
    e.experiment_id,
    0.04,
    0.04,
    20000,
    r.researcher_id
FROM noise_channels n
JOIN experiments e
    ON e.experiment_code = 'QEM-RUN-001'
JOIN researchers r
    ON r.email = 'researcher@example.org'
WHERE n.noise_name = 'bit-flip-channel-8pct';

INSERT INTO governance_policies(
    policy_name,
    maximum_noise,
    minimum_shots,
    maximum_standard_error,
    require_calibration
)
VALUES
(
    'STANDARD-RESEARCH-POLICY',
    0.20,
    1000,
    0.10,
    TRUE
),
(
    'STRICT-BENCHMARK-POLICY',
    0.10,
    10000,
    0.02,
    TRUE
);

INSERT INTO policy_allowed_methods(policy_id, method_id)
SELECT p.policy_id, m.method_id
FROM governance_policies p
CROSS JOIN mitigation_methods m
WHERE p.policy_name = 'STANDARD-RESEARCH-POLICY'
AND m.method_code IN (
    'NONE',
    'READOUT_CALIBRATION',
    'ZERO_NOISE_EXTRAPOLATION'
);

INSERT INTO policy_allowed_methods(policy_id, method_id)
SELECT p.policy_id, m.method_id
FROM governance_policies p
CROSS JOIN mitigation_methods m
WHERE p.policy_name = 'STRICT-BENCHMARK-POLICY'
AND m.method_code IN (
    'READOUT_CALIBRATION',
    'ZERO_NOISE_EXTRAPOLATION'
);

-- Record lifecycle changes automatically.
CREATE OR REPLACE FUNCTION log_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO audit_events(
            entity_type,
            entity_id,
            event_name,
            event_data
        )
        VALUES (
            'EXPERIMENT',
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
EXECUTE FUNCTION log_experiment_status();

-- Prevent completed experiments from silently changing state.
CREATE OR REPLACE FUNCTION enforce_experiment_lifecycle()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'FAILED', 'REJECTED')
       AND NEW.status IS DISTINCT FROM OLD.status THEN
        RAISE EXCEPTION
            'Terminal experiment state % cannot be changed',
            OLD.status;
    END IF;

    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = NOW();
    END IF;

    IF NEW.status = 'COMPLETED' AND NEW.completed_at IS NULL THEN
        NEW.completed_at = NOW();
    END IF;

    IF NEW.status = 'COMPLETED' AND NEW.started_at IS NULL THEN
        RAISE EXCEPTION
            'An experiment cannot complete without starting';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_lifecycle
BEFORE UPDATE ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_lifecycle();

-- Store the ideal result separately from noisy experimental observations.
CREATE OR REPLACE FUNCTION calculate_bias(
    p_estimate NUMERIC,
    p_ideal NUMERIC
)
RETURNS NUMERIC
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT p_estimate - p_ideal;
$$;

-- Insert an experiment result and compute its bias.
CREATE OR REPLACE PROCEDURE record_experiment_result(
    p_experiment_code VARCHAR,
    p_method mitigation_method,
    p_estimate NUMERIC,
    p_standard_error NUMERIC,
    p_shots INTEGER,
    p_resource_cost NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_experiment_id BIGINT;
    v_method_id BIGINT;
    v_ideal NUMERIC;
BEGIN
    SELECT
        e.experiment_id,
        e.ideal_expectation
    INTO
        v_experiment_id,
        v_ideal
    FROM experiments e
    WHERE e.experiment_code = p_experiment_code
      AND e.status IN ('RUNNING', 'COMPLETED');

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment % is not available for result recording',
            p_experiment_code;
    END IF;

    IF p_shots <= 0 OR p_standard_error < 0 OR p_resource_cost < 0 THEN
        RAISE EXCEPTION 'Invalid measurement result parameters';
    END IF;

    SELECT method_id
    INTO v_method_id
    FROM mitigation_methods
    WHERE method_code = p_method;

    INSERT INTO experiment_results(
        experiment_id,
        method_id,
        estimate,
        standard_error,
        shot_count,
        bias,
        resource_cost
    )
    VALUES (
        v_experiment_id,
        v_method_id,
        p_estimate,
        p_standard_error,
        p_shots,
        calculate_bias(p_estimate, v_ideal),
        p_resource_cost
    );
END;
$$;

-- Create a reusable result set.
CREATE OR REPLACE VIEW v_experiment_result_details AS
SELECT
    e.experiment_code,
    p.project_code,
    c.circuit_name,
    n.noise_category,
    n.error_probability,
    e.shots AS allocated_shots,
    m.method_code,
    r.estimate,
    r.standard_error,
    r.bias,
    r.shot_count,
    r.resource_cost,
    r.created_at
FROM experiment_results r
JOIN experiments e ON e.experiment_id = r.experiment_id
JOIN quantum_circuits c ON c.circuit_id = e.circuit_id
JOIN research_projects p ON p.project_id = c.project_id
JOIN noise_channels n ON n.noise_channel_id = e.noise_channel_id
JOIN mitigation_methods m ON m.method_id = r.method_id;

-- Evaluate whether a measurement result satisfies a policy.
CREATE OR REPLACE FUNCTION evaluate_eligibility(
    p_result_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    status eligibility_status,
    violations JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_result RECORD;
    v_policy RECORD;
    v_violations JSONB := '[]'::jsonb;
    v_method_allowed BOOLEAN;
    v_calibrated BOOLEAN;
BEGIN
    SELECT
        r.result_id,
        r.experiment_id,
        r.standard_error,
        r.shot_count,
        m.method_id,
        e.noise_channel_id,
        n.error_probability
    INTO v_result
    FROM experiment_results r
    JOIN experiments e ON e.experiment_id = r.experiment_id
    JOIN noise_channels n
        ON n.noise_channel_id = e.noise_channel_id
    JOIN mitigation_methods m ON m.method_id = r.method_id
    WHERE r.result_id = p_result_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Result % does not exist', p_result_id;
    END IF;

    SELECT *
    INTO v_policy
    FROM governance_policies
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active policy % does not exist', p_policy_id;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM policy_allowed_methods pam
        WHERE pam.policy_id = p_policy_id
          AND pam.method_id = v_result.method_id
    )
    INTO v_method_allowed;

    IF NOT v_method_allowed THEN
        v_violations = v_violations ||
            jsonb_build_array('Mitigation method not allowed');
    END IF;

    IF v_result.error_probability > v_policy.maximum_noise THEN
        v_violations = v_violations ||
            jsonb_build_array('Noise threshold exceeded');
    END IF;

    IF v_result.shot_count < v_policy.minimum_shots THEN
        v_violations = v_violations ||
            jsonb_build_array('Insufficient measurement shots');
    END IF;

    IF v_result.standard_error > v_policy.maximum_standard_error THEN
        v_violations = v_violations ||
            jsonb_build_array('Measurement uncertainty exceeded');
    END IF;

    IF v_policy.require_calibration THEN
        SELECT EXISTS (
            SELECT 1
            FROM calibration_records cr
            WHERE cr.noise_channel_id = v_result.noise_channel_id
              AND cr.calibrated_at > NOW() - INTERVAL '24 hours'
        )
        INTO v_calibrated;

        IF NOT v_calibrated THEN
            v_violations = v_violations ||
                jsonb_build_array('Recent calibration required');
        END IF;
    END IF;

    RETURN QUERY
    SELECT
        CASE
            WHEN jsonb_array_length(v_violations) = 0
                THEN 'ELIGIBLE'::eligibility_status
            ELSE 'INELIGIBLE'::eligibility_status
        END,
        v_violations;
END;
$$;

-- Record the evaluation as an auditable decision.
CREATE OR REPLACE PROCEDURE evaluate_and_record(
    p_result_id BIGINT,
    p_policy_id BIGINT,
    p_reviewer_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_experiment_id BIGINT;
    v_status eligibility_status;
    v_violations JSONB;
BEGIN
    SELECT experiment_id
    INTO v_experiment_id
    FROM experiment_results
    WHERE result_id = p_result_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown result ID';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM researchers
        WHERE researcher_id = p_reviewer_id
          AND active = TRUE
          AND role_name IN ('REVIEWER', 'PRINCIPAL_INVESTIGATOR')
    ) THEN
        RAISE EXCEPTION 'Reviewer is not authorized';
    END IF;

    SELECT e.status, e.violations
    INTO v_status, v_violations
    FROM evaluate_eligibility(p_result_id, p_policy_id) e;

    INSERT INTO eligibility_decisions(
        experiment_id,
        result_id,
        policy_id,
        status,
        violations,
        evaluated_by
    )
    VALUES (
        v_experiment_id,
        p_result_id,
        p_policy_id,
        v_status,
        v_violations,
        p_reviewer_id
    )
    ON CONFLICT (result_id, policy_id)
    DO UPDATE SET
        status = EXCLUDED.status,
        violations = EXCLUDED.violations,
        evaluated_by = EXCLUDED.evaluated_by,
        evaluated_at = NOW();

    INSERT INTO audit_events(
        entity_type,
        entity_id,
        event_name,
        event_data
    )
    VALUES (
        'EXPERIMENT_RESULT',
        p_result_id,
        'POLICY_EVALUATED',
        jsonb_build_object(
            'policy_id', p_policy_id,
            'status', v_status,
            'violations', v_violations,
            'reviewer_id', p_reviewer_id
        )
    );
END;
$$;

-- Register observations for the three noise scales.
INSERT INTO extrapolation_observations(
    experiment_id,
    method_id,
    noise_scale,
    observed_expectation,
    shot_count
)
SELECT
    e.experiment_id,
    m.method_id,
    observations.noise_scale,
    observations.observed_expectation,
    30000
FROM experiments e
JOIN mitigation_methods m
    ON m.method_code = 'ZERO_NOISE_EXTRAPOLATION'
CROSS JOIN (
    VALUES
        (1.0::NUMERIC, 0.84::NUMERIC),
        (1.5::NUMERIC, 0.76::NUMERIC),
        (2.0::NUMERIC, 0.68::NUMERIC)
) AS observations(noise_scale, observed_expectation)
WHERE e.experiment_code = 'QEM-RUN-001';

-- Demonstrate transaction-controlled experiment processing.
SAVEPOINT experiment_processing;

UPDATE experiments
SET status = 'RUNNING'
WHERE experiment_code = 'QEM-RUN-001'
  AND status = 'CREATED';

CALL record_experiment_result(
    'QEM-RUN-001',
    'NONE',
    0.773,
    0.005,
    30000,
    30000
);

CALL record_experiment_result(
    'QEM-RUN-001',
    'READOUT_CALIBRATION',
    0.840,
    0.006,
    30000,
    36000
);

CALL record_experiment_result(
    'QEM-RUN-001',
    'ZERO_NOISE_EXTRAPOLATION',
    0.920,
    0.009,
    90000,
    90000
);

UPDATE experiments
SET status = 'COMPLETED'
WHERE experiment_code = 'QEM-RUN-001'
  AND status = 'RUNNING';

-- The transaction is committed only after all result records are valid.
RELEASE SAVEPOINT experiment_processing;

-- Evaluate each result under the standard research policy.
CALL evaluate_and_record(
    (
        SELECT result_id
        FROM experiment_results r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE e.experiment_code = 'QEM-RUN-001'
          AND r.method_id = (
              SELECT method_id
              FROM mitigation_methods
              WHERE method_code = 'NONE'
          )
    ),
    (
        SELECT policy_id
        FROM governance_policies
        WHERE policy_name = 'STANDARD-RESEARCH-POLICY'
    ),
    (
        SELECT researcher_id
        FROM researchers
        WHERE email = 'reviewer@example.org'
    )
);

CALL evaluate_and_record(
    (
        SELECT result_id
        FROM experiment_results r
        JOIN experiments e ON e.experiment_id = r.experiment_id
        WHERE e.experiment_code = 'QEM-RUN-001'
          AND r.method_id = (
              SELECT method_id
              FROM mitigation_methods
              WHERE method_code = 'READOUT_CALIBRATION'
          )
    ),
    (
        SELECT policy_id
        FROM governance_policies
        WHERE policy_name = 'STANDARD-RESEARCH-POLICY'
    ),
    (
        SELECT researcher_id
        FROM researchers
        WHERE email = 'reviewer@example.org'
    )
);

-- Retrieval: detailed experiment measurements.
SELECT *
FROM v_experiment_result_details
ORDER BY experiment_code, method_code;

-- Validation: policy eligibility for every recorded result.
SELECT
    r.result_id,
    e.experiment_code,
    m.method_code,
    evaluation.status,
    evaluation.violations
FROM experiment_results r
JOIN experiments e ON e.experiment_id = r.experiment_id
JOIN mitigation_methods m ON m.method_id = r.method_id
CROSS JOIN LATERAL evaluate_eligibility(
    r.result_id,
    (
        SELECT policy_id
        FROM governance_policies
        WHERE policy_name = 'STANDARD-RESEARCH-POLICY'
    )
) AS evaluation
ORDER BY r.result_id;

-- Aggregation: method-level bias and uncertainty.
SELECT
    m.method_code,
    COUNT(*) AS result_count,
    ROUND(AVG(r.estimate), 6) AS average_estimate,
    ROUND(AVG(ABS(r.bias)), 6) AS average_absolute_bias,
    ROUND(AVG(r.standard_error), 6) AS average_uncertainty,
    SUM(r.resource_cost) AS total_resource_cost
FROM experiment_results r
JOIN mitigation_methods m ON m.method_id = r.method_id
GROUP BY m.method_code
ORDER BY average_absolute_bias;

-- Workflow reporting: experiment lifecycle.
SELECT
    status,
    COUNT(*) AS experiment_count,
    AVG(shots) AS average_shots
FROM experiments
GROUP BY status
ORDER BY status;

-- CTE: identify the lowest-bias method for each experiment.
WITH ranked_methods AS (
    SELECT
        e.experiment_code,
        m.method_code,
        ABS(r.bias) AS absolute_bias,
        r.standard_error,
        r.resource_cost,
        ROW_NUMBER() OVER (
            PARTITION BY e.experiment_id
            ORDER BY ABS(r.bias), r.resource_cost
        ) AS ranking
    FROM experiment_results r
    JOIN experiments e ON e.experiment_id = r.experiment_id
    JOIN mitigation_methods m ON m.method_id = r.method_id
)
SELECT
    experiment_code,
    method_code,
    absolute_bias,
    standard_error,
    resource_cost
FROM ranked_methods
WHERE ranking = 1;

-- Eligibility determination report.
SELECT
    e.experiment_code,
    m.method_code,
    gp.policy_name,
    ed.status,
    ed.violations,
    ed.evaluated_at
FROM eligibility_decisions ed
JOIN experiments e ON e.experiment_id = ed.experiment_id
JOIN experiment_results r ON r.result_id = ed.result_id
JOIN mitigation_methods m ON m.method_id = r.method_id
JOIN governance_policies gp ON gp.policy_id = ed.policy_id
ORDER BY ed.evaluated_at DESC;

-- Resource overhead for probabilistic error cancellation.
SELECT
    noise_name,
    error_probability,
    ROUND(
        (1.0 / (1.0 - 2.0 * error_probability))^2,
        4
    ) AS theoretical_sampling_overhead
FROM noise_channels
WHERE noise_category = 'BIT_FLIP'
  AND error_probability < 0.5;

COMMIT;
