/*
 * NISQ Era: Noisy Intermediate-Scale Quantum Computing
 *
 * PostgreSQL 15+
 *
 * Relational quantum experiment management platform.
 *
 * Models:
 *   Organizations
 *   Quantum processors
 *   Qubits
 *   Connectivity
 *   Gate calibration
 *   Quantum circuits
 *   Circuit gates
 *   Experiment submissions
 *   Noise models
 *   Device selection
 *   Execution jobs
 *   Measurement results
 *   Error budgets
 *   Experiment governance
 *
 * Run as a database owner with schema creation privileges.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS nisq;

SET search_path TO nisq, public;

CREATE TABLE IF NOT EXISTS organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    username VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    role VARCHAR(30) NOT NULL
        CHECK (role IN (
            'RESEARCHER',
            'ADMINISTRATOR',
            'OPERATOR',
            'AUDITOR'
        )),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (organization_id, username),
    UNIQUE (organization_id, email)
);

CREATE TABLE IF NOT EXISTS quantum_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    device_code VARCHAR(50) NOT NULL,
    device_name VARCHAR(150) NOT NULL,
    technology VARCHAR(30) NOT NULL
        CHECK (technology IN (
            'SUPERCONDUCTING',
            'TRAPPED_ION',
            'PHOTONIC',
            'NEUTRAL_ATOM',
            'OTHER'
        )),
    qubit_capacity INTEGER NOT NULL
        CHECK (qubit_capacity > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'ONLINE'
        CHECK (status IN (
            'ONLINE',
            'MAINTENANCE',
            'OFFLINE',
            'RETIRED'
        )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, device_code)
);

CREATE TABLE IF NOT EXISTS device_qubits (
    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id) ON DELETE CASCADE,
    qubit_index INTEGER NOT NULL CHECK (qubit_index >= 0),
    coherence_t1_us NUMERIC(14, 6)
        CHECK (coherence_t1_us IS NULL OR coherence_t1_us > 0),
    coherence_t2_us NUMERIC(14, 6)
        CHECK (coherence_t2_us IS NULL OR coherence_t2_us > 0),
    readout_error NUMERIC(10, 8) NOT NULL
        CHECK (readout_error BETWEEN 0 AND 1),
    last_calibrated_at TIMESTAMPTZ,
    PRIMARY KEY (device_id, qubit_index)
);

CREATE TABLE IF NOT EXISTS device_connectivity (
    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id) ON DELETE CASCADE,
    qubit_a INTEGER NOT NULL,
    qubit_b INTEGER NOT NULL,
    connectivity_type VARCHAR(20) NOT NULL DEFAULT 'DIRECT'
        CHECK (connectivity_type IN (
            'DIRECT',
            'SWAPPABLE'
        )),
    PRIMARY KEY (device_id, qubit_a, qubit_b),
    CHECK (qubit_a < qubit_b)
);

CREATE TABLE IF NOT EXISTS gate_calibrations (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),
    gate_type VARCHAR(20) NOT NULL
        CHECK (gate_type IN (
            'H', 'X', 'Y', 'Z', 'S', 'T',
            'CNOT', 'CZ', 'SWAP', 'RX', 'RY', 'RZ'
        )),
    qubit_a INTEGER NOT NULL,
    qubit_b INTEGER,
    gate_error NUMERIC(12, 10) NOT NULL
        CHECK (gate_error BETWEEN 0 AND 1),
    gate_duration_ns NUMERIC(14, 4) NOT NULL
        CHECK (gate_duration_ns > 0),
    calibration_version INTEGER NOT NULL
        CHECK (calibration_version > 0),
    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    calibrated_by BIGINT REFERENCES users(user_id),
    CHECK (
        (gate_type IN ('CNOT', 'CZ', 'SWAP')
            AND qubit_b IS NOT NULL
            AND qubit_a <> qubit_b)
        OR
        (gate_type NOT IN ('CNOT', 'CZ', 'SWAP')
            AND qubit_b IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_calibration_device_gate
ON gate_calibrations (
    device_id,
    gate_type,
    calibrated_at DESC
);

CREATE TABLE IF NOT EXISTS noise_models (
    noise_model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    model_name VARCHAR(120) NOT NULL,
    single_qubit_error NUMERIC(12, 10) NOT NULL
        CHECK (single_qubit_error BETWEEN 0 AND 1),
    two_qubit_error NUMERIC(12, 10) NOT NULL
        CHECK (two_qubit_error BETWEEN 0 AND 1),
    readout_error NUMERIC(12, 10) NOT NULL
        CHECK (readout_error BETWEEN 0 AND 1),
    relaxation_error NUMERIC(12, 10) NOT NULL
        CHECK (relaxation_error BETWEEN 0 AND 1),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, model_name)
);

CREATE TABLE IF NOT EXISTS quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    owner_id BIGINT NOT NULL
        REFERENCES users(user_id),
    circuit_name VARCHAR(150) NOT NULL,
    circuit_type VARCHAR(40) NOT NULL
        CHECK (circuit_type IN (
            'BELL',
            'GHZ',
            'VQE',
            'QAOA',
            'QUANTUM_SIMULATION',
            'CUSTOM'
        )),
    qubit_count INTEGER NOT NULL
        CHECK (qubit_count > 0),
    circuit_depth INTEGER NOT NULL DEFAULT 0
        CHECK (circuit_depth >= 0),
    version INTEGER NOT NULL DEFAULT 1
        CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, circuit_name, version)
);

CREATE TABLE IF NOT EXISTS circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL
        CHECK (sequence_number > 0),
    gate_type VARCHAR(20) NOT NULL
        CHECK (gate_type IN (
            'H', 'X', 'Y', 'Z', 'S', 'T',
            'CNOT', 'CZ', 'SWAP', 'RX', 'RY', 'RZ'
        )),
    target_qubit INTEGER NOT NULL
        CHECK (target_qubit >= 0),
    control_qubit INTEGER,
    rotation_angle NUMERIC(16, 10),
    UNIQUE (circuit_id, sequence_number),
    CHECK (
        (gate_type IN ('CNOT', 'CZ', 'SWAP')
            AND control_qubit IS NOT NULL
            AND control_qubit <> target_qubit)
        OR
        (gate_type NOT IN ('CNOT', 'CZ', 'SWAP')
            AND control_qubit IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_circuit_gates_sequence
ON circuit_gates(circuit_id, sequence_number);

CREATE TABLE IF NOT EXISTS approval_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    policy_name VARCHAR(120) NOT NULL,
    maximum_gate_error NUMERIC(12, 10) NOT NULL
        CHECK (maximum_gate_error BETWEEN 0 AND 1),
    minimum_success_probability NUMERIC(12, 10) NOT NULL
        CHECK (minimum_success_probability BETWEEN 0 AND 1),
    maximum_coherence_ratio NUMERIC(12, 10) NOT NULL
        CHECK (maximum_coherence_ratio > 0),
    minimum_calibration_version INTEGER NOT NULL DEFAULT 1
        CHECK (minimum_calibration_version > 0),
    maximum_circuit_depth INTEGER NOT NULL
        CHECK (maximum_circuit_depth > 0),
    require_online_device BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, policy_name)
);

CREATE TABLE IF NOT EXISTS experiment_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id),
    requested_by BIGINT NOT NULL
        REFERENCES users(user_id),
    selected_device_id BIGINT
        REFERENCES quantum_devices(device_id),
    noise_model_id BIGINT
        REFERENCES noise_models(noise_model_id),
    policy_id BIGINT NOT NULL
        REFERENCES approval_policies(policy_id),
    shots INTEGER NOT NULL
        CHECK (shots BETWEEN 1 AND 10000000),
    status VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED'
        CHECK (status IN (
            'SUBMITTED',
            'VALIDATING',
            'APPROVED',
            'REJECTED',
            'QUEUED',
            'RUNNING',
            'COMPLETED',
            'FAILED',
            'CANCELLED'
        )),
    estimated_success_probability NUMERIC(12, 10)
        CHECK (
            estimated_success_probability IS NULL
            OR estimated_success_probability BETWEEN 0 AND 1
        ),
    rejection_reason TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    CHECK (
        (status <> 'COMPLETED' OR completed_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_jobs_status_submitted
ON experiment_jobs(status, submitted_at);

CREATE INDEX IF NOT EXISTS idx_jobs_device_status
ON experiment_jobs(selected_device_id, status);

CREATE INDEX IF NOT EXISTS idx_jobs_organization
ON experiment_jobs(organization_id, submitted_at DESC);

CREATE TABLE IF NOT EXISTS measurement_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL
        REFERENCES experiment_jobs(job_id) ON DELETE CASCADE,
    bitstring VARCHAR(100) NOT NULL,
    occurrence_count BIGINT NOT NULL
        CHECK (occurrence_count >= 0),
    probability NUMERIC(16, 12) NOT NULL
        CHECK (probability BETWEEN 0 AND 1),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, bitstring)
);

CREATE TABLE IF NOT EXISTS eligibility_audits (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL
        REFERENCES experiment_jobs(job_id) ON DELETE CASCADE,
    policy_id BIGINT NOT NULL
        REFERENCES approval_policies(policy_id),
    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),
    eligible BOOLEAN NOT NULL,
    estimated_gate_success NUMERIC(12, 10)
        CHECK (
            estimated_gate_success IS NULL OR
            estimated_gate_success BETWEEN 0 AND 1
        ),
    estimated_readout_success NUMERIC(12, 10)
        CHECK (
            estimated_readout_success IS NULL OR
            estimated_readout_success BETWEEN 0 AND 1
        ),
    coherence_ratio NUMERIC(16, 10),
    reasons JSONB NOT NULL DEFAULT '[]'::JSONB,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audits_job_time
ON eligibility_audits(job_id, evaluated_at DESC);

/*
 * Enforce that circuit gates reference valid qubit indices.
 */

CREATE OR REPLACE FUNCTION validate_circuit_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO v_qubits
    FROM quantum_circuits
    WHERE circuit_id = NEW.circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit % does not exist', NEW.circuit_id;
    END IF;

    IF NEW.target_qubit >= v_qubits THEN
        RAISE EXCEPTION 'Target qubit exceeds circuit capacity';
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND NEW.control_qubit >= v_qubits THEN
        RAISE EXCEPTION 'Control qubit exceeds circuit capacity';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_circuit_gate
ON circuit_gates;

CREATE TRIGGER trg_validate_circuit_gate
BEFORE INSERT OR UPDATE ON circuit_gates
FOR EACH ROW
EXECUTE FUNCTION validate_circuit_gate();

/*
 * Prevent duplicate physical connectivity edges.
 */

CREATE OR REPLACE FUNCTION normalize_connectivity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_capacity INTEGER;
BEGIN
    SELECT qubit_capacity
    INTO v_capacity
    FROM quantum_devices
    WHERE device_id = NEW.device_id;

    IF NEW.qubit_a < 0 OR NEW.qubit_b < 0
       OR NEW.qubit_a >= v_capacity
       OR NEW.qubit_b >= v_capacity THEN
        RAISE EXCEPTION 'Connectivity exceeds device capacity';
    END IF;

    IF NEW.qubit_a > NEW.qubit_b THEN
        RAISE EXCEPTION
            'Connectivity must use ascending qubit indices';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_normalize_connectivity
ON device_connectivity;

CREATE TRIGGER trg_normalize_connectivity
BEFORE INSERT OR UPDATE ON device_connectivity
FOR EACH ROW
EXECUTE FUNCTION normalize_connectivity();

/*
 * Calculate a conservative analytical success estimate.
 *
 * This estimate assumes independent gate and readout errors.
 * It is not a quantum-state fidelity calculation.
 */

CREATE OR REPLACE FUNCTION estimate_circuit_success(
    p_circuit_id BIGINT,
    p_device_id BIGINT,
    p_coherence_ratio NUMERIC DEFAULT 0
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_one_count INTEGER;
    v_two_count INTEGER;
    v_qubits INTEGER;
    v_single_error NUMERIC;
    v_two_error NUMERIC;
    v_readout_error NUMERIC;
    v_gate_success NUMERIC;
    v_readout_success NUMERIC;
    v_coherence NUMERIC;
BEGIN
    SELECT qubit_count
    INTO v_qubits
    FROM quantum_circuits
    WHERE circuit_id = p_circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit not found';
    END IF;

    SELECT
        COALESCE(COUNT(*) FILTER (
            WHERE gate_type NOT IN ('CNOT', 'CZ', 'SWAP')
        ), 0),
        COALESCE(COUNT(*) FILTER (
            WHERE gate_type IN ('CNOT', 'CZ', 'SWAP')
        ), 0)
    INTO v_one_count, v_two_count
    FROM circuit_gates
    WHERE circuit_id = p_circuit_id;

    SELECT
        MAX(gate_error) FILTER (
            WHERE gate_type NOT IN ('CNOT', 'CZ', 'SWAP')
        ),
        MAX(gate_error) FILTER (
            WHERE gate_type IN ('CNOT', 'CZ', 'SWAP')
        )
    INTO v_single_error, v_two_error
    FROM gate_calibrations
    WHERE device_id = p_device_id;

    SELECT AVG(readout_error)
    INTO v_readout_error
    FROM device_qubits
    WHERE device_id = p_device_id;

    IF v_single_error IS NULL
       OR v_readout_error IS NULL THEN
        RETURN NULL;
    END IF;

    v_two_error := COALESCE(v_two_error, v_single_error);

    v_gate_success :=
        POWER(1 - v_single_error, v_one_count) *
        POWER(1 - v_two_error, v_two_count);

    v_readout_success :=
        POWER(1 - v_readout_error, v_qubits);

    v_coherence :=
        EXP(-GREATEST(0, p_coherence_ratio));

    RETURN GREATEST(
        0,
        LEAST(
            1,
            v_gate_success *
            v_readout_success *
            v_coherence
        )
    );
END;
$$;

/*
 * Determine circuit eligibility using a selected device and policy.
 */

CREATE OR REPLACE FUNCTION evaluate_experiment(
    p_circuit_id BIGINT,
    p_device_id BIGINT,
    p_policy_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    estimated_success NUMERIC,
    reasons JSONB
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_circuit quantum_circuits%ROWTYPE;
    v_device quantum_devices%ROWTYPE;
    v_policy approval_policies%ROWTYPE;
    v_max_error NUMERIC;
    v_min_calibration INTEGER;
    v_estimate NUMERIC;
    v_reasons JSONB := '[]'::JSONB;
    v_gate_count INTEGER;
BEGIN
    SELECT * INTO v_circuit
    FROM quantum_circuits
    WHERE circuit_id = p_circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit not found';
    END IF;

    SELECT * INTO v_device
    FROM quantum_devices
    WHERE device_id = p_device_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Device not found';
    END IF;

    SELECT * INTO v_policy
    FROM approval_policies
    WHERE policy_id = p_policy_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Active policy not found';
    END IF;

    IF v_policy.organization_id <> v_circuit.organization_id
       OR v_policy.organization_id <> v_device.organization_id THEN
        RAISE EXCEPTION 'Cross-organization execution is prohibited';
    END IF;

    IF v_device.status <> 'ONLINE'
       AND v_policy.require_online_device THEN
        v_reasons := v_reasons ||
            '["Device is not online"]'::JSONB;
    END IF;

    IF v_circuit.qubit_count > v_device.qubit_capacity THEN
        v_reasons := v_reasons ||
            '["Insufficient qubit capacity"]'::JSONB;
    END IF;

    SELECT COUNT(*)
    INTO v_gate_count
    FROM circuit_gates
    WHERE circuit_id = p_circuit_id;

    IF v_gate_count = 0 THEN
        v_reasons := v_reasons ||
            '["Circuit has no gates"]'::JSONB;
    END IF;

    SELECT MAX(gate_error), MIN(calibration_version)
    INTO v_max_error, v_min_calibration
    FROM gate_calibrations
    WHERE device_id = p_device_id;

    IF v_max_error IS NULL OR
       v_max_error > v_policy.maximum_gate_error THEN
        v_reasons := v_reasons ||
            '["Gate calibration exceeds policy"]'::JSONB;
    END IF;

    IF v_min_calibration IS NULL OR
       v_min_calibration < v_policy.minimum_calibration_version THEN
        v_reasons := v_reasons ||
            '["Calibration version is insufficient"]'::JSONB;
    END IF;

    v_estimate := estimate_circuit_success(
        p_circuit_id,
        p_device_id,
        0
    );

    IF v_estimate IS NULL THEN
        v_reasons := v_reasons ||
            '["Incomplete device calibration"]'::JSONB;
    ELSIF v_estimate < v_policy.minimum_success_probability THEN
        v_reasons := v_reasons ||
            '["Estimated success is below policy threshold"]'::JSONB;
    END IF;

    RETURN QUERY
    SELECT
        jsonb_array_length(v_reasons) = 0,
        v_estimate,
        v_reasons;
END;
$$;

/*
 * Queue an experiment with organization isolation and eligibility checks.
 */

CREATE OR REPLACE PROCEDURE submit_experiment(
    p_organization_id BIGINT,
    p_circuit_id BIGINT,
    p_user_id BIGINT,
    p_device_id BIGINT,
    p_noise_model_id BIGINT,
    p_policy_id BIGINT,
    p_shots INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_eligible BOOLEAN;
    v_estimate NUMERIC;
    v_reasons JSONB;
    v_job_id BIGINT;
    v_device quantum_devices%ROWTYPE;
BEGIN
    IF p_shots < 1 OR p_shots > 10000000 THEN
        RAISE EXCEPTION 'Invalid shot count';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM users
        WHERE user_id = p_user_id
          AND organization_id = p_organization_id
          AND active = TRUE
          AND role IN ('RESEARCHER', 'ADMINISTRATOR', 'OPERATOR')
    ) THEN
        RAISE EXCEPTION 'User is not authorized to submit experiments';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM quantum_circuits
        WHERE circuit_id = p_circuit_id
          AND organization_id = p_organization_id
          AND owner_id = p_user_id
    ) THEN
        RAISE EXCEPTION 'Circuit ownership or organization mismatch';
    END IF;

    SELECT * INTO v_device
    FROM quantum_devices
    WHERE device_id = p_device_id
      AND organization_id = p_organization_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Device organization mismatch';
    END IF;

    SELECT * INTO v_eligible, v_estimate, v_reasons
    FROM evaluate_experiment(
        p_circuit_id,
        p_device_id,
        p_policy_id
    );

    INSERT INTO experiment_jobs (
        organization_id,
        circuit_id,
        requested_by,
        selected_device_id,
        noise_model_id,
        policy_id,
        shots,
        status,
        estimated_success_probability,
        rejection_reason
    )
    VALUES (
        p_organization_id,
        p_circuit_id,
        p_user_id,
        p_device_id,
        p_noise_model_id,
        p_policy_id,
        p_shots,
        CASE WHEN v_eligible THEN 'APPROVED' ELSE 'REJECTED' END,
        v_estimate,
        CASE
            WHEN v_eligible THEN NULL
            ELSE v_reasons::TEXT
        END
    )
    RETURNING job_id INTO v_job_id;

    INSERT INTO eligibility_audits (
        job_id,
        policy_id,
        device_id,
        eligible,
        estimated_gate_success,
        estimated_readout_success,
        coherence_ratio,
        reasons
    )
    SELECT
        v_job_id,
        p_policy_id,
        p_device_id,
        v_eligible,
        NULL,
        NULL,
        NULL,
        v_reasons;

    RAISE NOTICE
        'Experiment job % submitted with status %',
        v_job_id,
        CASE WHEN v_eligible THEN 'APPROVED' ELSE 'REJECTED' END;
END;
$$;

/*
 * Record measurement outcomes.
 * Result bitstrings must match circuit width.
 */

CREATE OR REPLACE FUNCTION validate_measurement_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_qubits INTEGER;
BEGIN
    SELECT c.qubit_count
    INTO v_qubits
    FROM experiment_jobs j
    JOIN quantum_circuits c
      ON c.circuit_id = j.circuit_id
    WHERE j.job_id = NEW.job_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment job not found';
    END IF;

    IF LENGTH(NEW.bitstring) <> v_qubits
       OR NEW.bitstring !~ '^[01]+$' THEN
        RAISE EXCEPTION 'Invalid measurement bitstring';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_measurement
ON measurement_results;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT OR UPDATE ON measurement_results
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_result();

/*
 * Read-only reporting view.
 */

CREATE OR REPLACE VIEW experiment_overview AS
SELECT
    j.job_id,
    o.organization_name,
    u.username AS submitted_by,
    c.circuit_name,
    c.circuit_type,
    c.qubit_count,
    c.circuit_depth,
    d.device_name,
    d.technology,
    j.shots,
    j.status,
    j.estimated_success_probability,
    j.submitted_at,
    j.completed_at
FROM experiment_jobs j
JOIN organizations o
    ON o.organization_id = j.organization_id
JOIN users u
    ON u.user_id = j.requested_by
JOIN quantum_circuits c
    ON c.circuit_id = j.circuit_id
LEFT JOIN quantum_devices d
    ON d.device_id = j.selected_device_id;

/*
 * Sample records.
 */

INSERT INTO organizations (organization_name)
VALUES
    ('Quantum Research Laboratory'),
    ('Applied Quantum Systems')
ON CONFLICT DO NOTHING;

INSERT INTO users (
    organization_id,
    username,
    email,
    role
)
SELECT organization_id, 'researcher_01',
       'researcher01@example.org', 'RESEARCHER'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO users (
    organization_id,
    username,
    email,
    role
)
SELECT organization_id, 'operator_01',
       'operator01@example.org', 'OPERATOR'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO users (
    organization_id,
    username,
    email,
    role
)
SELECT organization_id, 'auditor_01',
       'auditor01@example.org', 'AUDITOR'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO quantum_devices (
    organization_id,
    device_code,
    device_name,
    technology,
    qubit_capacity,
    status
)
SELECT
    organization_id,
    'QPU-ALPHA',
    'Superconducting Processor Alpha',
    'SUPERCONDUCTING',
    5,
    'ONLINE'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO quantum_devices (
    organization_id,
    device_code,
    device_name,
    technology,
    qubit_capacity,
    status
)
SELECT
    organization_id,
    'QPU-BETA',
    'Superconducting Processor Beta',
    'SUPERCONDUCTING',
    8,
    'ONLINE'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO quantum_devices (
    organization_id,
    device_code,
    device_name,
    technology,
    qubit_capacity,
    status
)
SELECT
    organization_id,
    'QPU-MAINT',
    'Maintenance Processor',
    'TRAPPED_ION',
    10,
    'MAINTENANCE'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

/*
 * Generate physical qubit inventory.
 */

INSERT INTO device_qubits (
    device_id,
    qubit_index,
    coherence_t1_us,
    coherence_t2_us,
    readout_error,
    last_calibrated_at
)
SELECT
    d.device_id,
    q.qubit_index,
    100.0,
    80.0,
    0.02,
    CURRENT_TIMESTAMP
FROM quantum_devices d
CROSS JOIN LATERAL
    generate_series(0, d.qubit_capacity - 1) AS q(qubit_index)
WHERE d.device_code IN ('QPU-ALPHA', 'QPU-BETA', 'QPU-MAINT')
ON CONFLICT DO NOTHING;

/*
 * Connectivity records.
 */

INSERT INTO device_connectivity (
    device_id,
    qubit_a,
    qubit_b
)
SELECT
    d.device_id,
    edge.qubit_a,
    edge.qubit_b
FROM quantum_devices d
CROSS JOIN (
    VALUES
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7)
) AS edge(qubit_a, qubit_b)
WHERE d.device_code = 'QPU-BETA'
  AND edge.qubit_b < d.qubit_capacity
ON CONFLICT DO NOTHING;

INSERT INTO device_connectivity (
    device_id,
    qubit_a,
    qubit_b
)
SELECT
    d.device_id,
    edge.qubit_a,
    edge.qubit_b
FROM quantum_devices d
CROSS JOIN (
    VALUES
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4)
) AS edge(qubit_a, qubit_b)
WHERE d.device_code = 'QPU-ALPHA'
ON CONFLICT DO NOTHING;

/*
 * Gate calibrations.
 */

INSERT INTO gate_calibrations (
    device_id,
    gate_type,
    qubit_a,
    qubit_b,
    gate_error,
    gate_duration_ns,
    calibration_version
)
SELECT
    d.device_id,
    calibration.gate_type,
    calibration.qubit_a,
    calibration.qubit_b,
    calibration.gate_error,
    calibration.duration,
    3
FROM quantum_devices d
CROSS JOIN (
    VALUES
        ('H', 0, NULL::INTEGER, 0.001::NUMERIC, 50.0::NUMERIC),
        ('X', 0, NULL::INTEGER, 0.001::NUMERIC, 50.0::NUMERIC),
        ('Z', 0, NULL::INTEGER, 0.001::NUMERIC, 50.0::NUMERIC),
        ('CNOT', 0, 1, 0.009::NUMERIC, 250.0::NUMERIC),
        ('CZ', 0, 1, 0.010::NUMERIC, 250.0::NUMERIC)
) AS calibration(
    gate_type,
    qubit_a,
    qubit_b,
    gate_error,
    duration
)
WHERE d.device_code = 'QPU-ALPHA'
ON CONFLICT DO NOTHING;

INSERT INTO gate_calibrations (
    device_id,
    gate_type,
    qubit_a,
    qubit_b,
    gate_error,
    gate_duration_ns,
    calibration_version
)
SELECT
    d.device_id,
    calibration.gate_type,
    calibration.qubit_a,
    calibration.qubit_b,
    calibration.gate_error,
    calibration.duration,
    4
FROM quantum_devices d
CROSS JOIN (
    VALUES
        ('H', 0, NULL::INTEGER, 0.002::NUMERIC, 40.0::NUMERIC),
        ('X', 0, NULL::INTEGER, 0.002::NUMERIC, 40.0::NUMERIC),
        ('Z', 0, NULL::INTEGER, 0.002::NUMERIC, 40.0::NUMERIC),
        ('CNOT', 0, 1, 0.015::NUMERIC, 220.0::NUMERIC),
        ('CZ', 0, 1, 0.016::NUMERIC, 220.0::NUMERIC)
) AS calibration(
    gate_type,
    qubit_a,
    qubit_b,
    gate_error,
    duration
)
WHERE d.device_code = 'QPU-BETA'
ON CONFLICT DO NOTHING;

INSERT INTO noise_models (
    organization_id,
    model_name,
    single_qubit_error,
    two_qubit_error,
    readout_error,
    relaxation_error,
    description
)
SELECT
    organization_id,
    'STANDARD-NISQ',
    0.001,
    0.009,
    0.02,
    0.001,
    'Baseline stochastic noise model'
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

INSERT INTO approval_policies (
    organization_id,
    policy_name,
    maximum_gate_error,
    minimum_success_probability,
    maximum_coherence_ratio,
    minimum_calibration_version,
    maximum_circuit_depth,
    require_online_device
)
SELECT
    organization_id,
    'RESEARCH-STRICT',
    0.05,
    0.50,
    0.50,
    2,
    100,
    TRUE
FROM organizations
WHERE organization_name = 'Quantum Research Laboratory'
ON CONFLICT DO NOTHING;

/*
 * Register Bell and GHZ circuits.
 */

INSERT INTO quantum_circuits (
    organization_id,
    owner_id,
    circuit_name,
    circuit_type,
    qubit_count,
    circuit_depth
)
SELECT
    o.organization_id,
    u.user_id,
    'Bell State Preparation',
    'BELL',
    2,
    2
FROM organizations o
JOIN users u
    ON u.organization_id = o.organization_id
WHERE o.organization_name = 'Quantum Research Laboratory'
  AND u.username = 'researcher_01'
ON CONFLICT DO NOTHING;

INSERT INTO quantum_circuits (
    organization_id,
    owner_id,
    circuit_name,
    circuit_type,
    qubit_count,
    circuit_depth
)
SELECT
    o.organization_id,
    u.user_id,
    'Four Qubit GHZ State',
    'GHZ',
    4,
    4
FROM organizations o
JOIN users u
    ON u.organization_id = o.organization_id
WHERE o.organization_name = 'Quantum Research Laboratory'
  AND u.username = 'researcher_01'
ON CONFLICT DO NOTHING;

/*
 * Insert Bell circuit gates.
 */

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit,
    control_qubit
)
SELECT
    c.circuit_id,
    gate.sequence_number,
    gate.gate_type,
    gate.target_qubit,
    gate.control_qubit
FROM quantum_circuits c
CROSS JOIN (
    VALUES
        (1, 'H', 0, NULL::INTEGER),
        (2, 'CNOT', 1, 0)
) AS gate(
    sequence_number,
    gate_type,
    target_qubit,
    control_qubit
)
WHERE c.circuit_name = 'Bell State Preparation'
ON CONFLICT DO NOTHING;

/*
 * Insert GHZ circuit gates.
 */

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit,
    control_qubit
)
SELECT
    c.circuit_id,
    gate.sequence_number,
    gate.gate_type,
    gate.target_qubit,
    gate.control_qubit
FROM quantum_circuits c
CROSS JOIN (
    VALUES
        (1, 'H', 0, NULL::INTEGER),
        (2, 'CNOT', 1, 0),
        (3, 'CNOT', 2, 1),
        (4, 'CNOT', 3, 2)
) AS gate(
    sequence_number,
    gate_type,
    target_qubit,
    control_qubit
)
WHERE c.circuit_name = 'Four Qubit GHZ State'
ON CONFLICT DO NOTHING;

/*
 * Submit sample experiments.
 */

DO $$
DECLARE
    v_org BIGINT;
    v_user BIGINT;
    v_policy BIGINT;
    v_noise BIGINT;
    v_alpha BIGINT;
    v_bell BIGINT;
    v_ghz BIGINT;
BEGIN
    SELECT organization_id INTO v_org
    FROM organizations
    WHERE organization_name = 'Quantum Research Laboratory';

    SELECT user_id INTO v_user
    FROM users
    WHERE organization_id = v_org
      AND username = 'researcher_01';

    SELECT policy_id INTO v_policy
    FROM approval_policies
    WHERE organization_id = v_org
      AND policy_name = 'RESEARCH-STRICT';

    SELECT noise_model_id INTO v_noise
    FROM noise_models
    WHERE organization_id = v_org
      AND model_name = 'STANDARD-NISQ';

    SELECT device_id INTO v_alpha
    FROM quantum_devices
    WHERE organization_id = v_org
      AND device_code = 'QPU-ALPHA';

    SELECT circuit_id INTO v_bell
    FROM quantum_circuits
    WHERE organization_id = v_org
      AND circuit_name = 'Bell State Preparation';

    SELECT circuit_id INTO v_ghz
    FROM quantum_circuits
    WHERE organization_id = v_org
      AND circuit_name = 'Four Qubit GHZ State';

    IF NOT EXISTS (
        SELECT 1 FROM experiment_jobs
        WHERE circuit_id = v_bell
          AND selected_device_id = v_alpha
    ) THEN
        CALL submit_experiment(
            v_org, v_bell, v_user, v_alpha,
            v_noise, v_policy, 5000
        );
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM experiment_jobs
        WHERE circuit_id = v_ghz
          AND selected_device_id = v_alpha
    ) THEN
        CALL submit_experiment(
            v_org, v_ghz, v_user, v_alpha,
            v_noise, v_policy, 5000
        );
    END IF;
END;
$$;

/*
 * Demonstrate execution lifecycle processing.
 */

CREATE OR REPLACE PROCEDURE process_approved_jobs()
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE experiment_jobs
    SET status = 'QUEUED'
    WHERE status = 'APPROVED'
      AND selected_device_id IS NOT NULL;

    UPDATE experiment_jobs
    SET
        status = 'RUNNING',
        started_at = CURRENT_TIMESTAMP
    WHERE status = 'QUEUED';

    UPDATE experiment_jobs
    SET
        status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE status = 'RUNNING';
END;
$$;

CALL process_approved_jobs();

/*
 * Measurement records for the Bell experiment.
 */

INSERT INTO measurement_results (
    job_id,
    bitstring,
    occurrence_count,
    probability
)
SELECT
    j.job_id,
    measurement.bitstring,
    measurement.occurrences,
    measurement.probability
FROM experiment_jobs j
JOIN quantum_circuits c
    ON c.circuit_id = j.circuit_id
CROSS JOIN (
    VALUES
        ('00', 2480, 0.496),
        ('11', 2520, 0.504)
) AS measurement(
    bitstring,
    occurrences,
    probability
)
WHERE c.circuit_name = 'Bell State Preparation'
  AND j.status = 'COMPLETED'
ON CONFLICT (job_id, bitstring)
DO UPDATE SET
    occurrence_count = EXCLUDED.occurrence_count,
    probability = EXCLUDED.probability;

/*
 * Retrieval: experiment inventory.
 */

SELECT *
FROM experiment_overview
ORDER BY submitted_at DESC;

/*
 * Validation: circuit gate count and resource information.
 */

SELECT
    c.circuit_name,
    c.qubit_count,
    COUNT(g.gate_id) AS gate_count,
    COUNT(g.gate_id) FILTER (
        WHERE g.gate_type IN ('CNOT', 'CZ', 'SWAP')
    ) AS two_qubit_gate_count,
    COUNT(g.gate_id) FILTER (
        WHERE g.gate_type NOT IN ('CNOT', 'CZ', 'SWAP')
    ) AS single_qubit_gate_count
FROM quantum_circuits c
LEFT JOIN circuit_gates g
    ON g.circuit_id = c.circuit_id
GROUP BY c.circuit_id, c.circuit_name, c.qubit_count;

/*
 * Aggregation: processor inventory.
 */

SELECT
    d.device_name,
    d.technology,
    d.status,
    d.qubit_capacity,
    COUNT(DISTINCT j.job_id) AS experiment_count,
    AVG(j.estimated_success_probability) AS average_estimated_success
FROM quantum_devices d
LEFT JOIN experiment_jobs j
    ON j.selected_device_id = d.device_id
GROUP BY d.device_id
ORDER BY experiment_count DESC;

/*
 * Evaluation: compare gate calibration error.
 */

SELECT
    d.device_name,
    g.gate_type,
    MIN(g.gate_error) AS best_observed_error,
    MAX(g.gate_error) AS worst_observed_error,
    AVG(g.gate_error) AS mean_error
FROM quantum_devices d
JOIN gate_calibrations g
    ON g.device_id = d.device_id
GROUP BY d.device_id, d.device_name, g.gate_type
ORDER BY d.device_name, g.gate_type;

/*
 * Eligibility: inspect all current experiment decisions.
 */

SELECT
    j.job_id,
    c.circuit_name,
    d.device_name,
    a.eligible,
    a.reasons,
    a.evaluated_at
FROM eligibility_audits a
JOIN experiment_jobs j
    ON j.job_id = a.job_id
JOIN quantum_circuits c
    ON c.circuit_id = j.circuit_id
JOIN quantum_devices d
    ON d.device_id = a.device_id
ORDER BY a.evaluated_at DESC;

/*
 * Reporting: measurement distribution.
 */

SELECT
    c.circuit_name,
    r.bitstring,
    SUM(r.occurrence_count) AS observations,
    AVG(r.probability) AS recorded_probability
FROM measurement_results r
JOIN experiment_jobs j
    ON j.job_id = r.job_id
JOIN quantum_circuits c
    ON c.circuit_id = j.circuit_id
GROUP BY c.circuit_name, r.bitstring
ORDER BY c.circuit_name, r.bitstring;

/*
 * CTE: identify experiments with poor estimated success.
 */

WITH experiment_quality AS (
    SELECT
        job_id,
        circuit_id,
        selected_device_id,
        estimated_success_probability,
        status
    FROM experiment_jobs
),
quality_classification AS (
    SELECT
        job_id,
        CASE
            WHEN estimated_success_probability >= 0.90
                THEN 'HIGH'
            WHEN estimated_success_probability >= 0.50
                THEN 'MODERATE'
            ELSE 'LOW'
        END AS quality_category
    FROM experiment_quality
)
SELECT
    q.job_id,
    c.circuit_name,
    q.quality_category
FROM quality_classification q
JOIN experiment_jobs j
    ON j.job_id = q.job_id
JOIN quantum_circuits c
    ON c.circuit_id = j.circuit_id
ORDER BY q.job_id;

/*
 * Transaction demonstration:
 * A rejected experiment must not create partial audit records.
 * This transaction deliberately rolls back.
 */

SAVEPOINT before_rejected_experiment;

DO $$
DECLARE
    v_org BIGINT;
    v_user BIGINT;
    v_policy BIGINT;
    v_noise BIGINT;
    v_device BIGINT;
    v_circuit BIGINT;
BEGIN
    SELECT organization_id INTO v_org
    FROM organizations
    WHERE organization_name = 'Quantum Research Laboratory';

    SELECT user_id INTO v_user
    FROM users
    WHERE organization_id = v_org
      AND username = 'researcher_01';

    SELECT policy_id INTO v_policy
    FROM approval_policies
    WHERE organization_id = v_org
      AND policy_name = 'RESEARCH-STRICT';

    SELECT noise_model_id INTO v_noise
    FROM noise_models
    WHERE organization_id = v_org
      AND model_name = 'STANDARD-NISQ';

    SELECT device_id INTO v_device
    FROM quantum_devices
    WHERE organization_id = v_org
      AND device_code = 'QPU-MAINT';

    SELECT circuit_id INTO v_circuit
    FROM quantum_circuits
    WHERE organization_id = v_org
      AND circuit_name = 'Bell State Preparation';

    CALL submit_experiment(
        v_org,
        v_circuit,
        v_user,
        v_device,
        v_noise,
        v_policy,
        1000
    );
END;
$$;

ROLLBACK TO SAVEPOINT before_rejected_experiment;

COMMIT;
