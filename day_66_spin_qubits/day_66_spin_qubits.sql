/*
 * SPIN QUBITS IN SEMICONDUCTOR QUANTUM SYSTEMS
 *
 * PostgreSQL 15+
 *
 * Models:
 * - Semiconductor quantum devices
 * - Quantum-dot architectures
 * - Electron spin qubits
 * - Device calibration
 * - Control pulses
 * - Exchange interactions
 * - Experiments and approvals
 * - Measurement records
 * - Coherence characterization
 * - Operator permissions
 * - Experiment eligibility
 *
 * All measurements and calibration values are simulated example data.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;

SET search_path TO quantum_lab, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE semiconductor_material AS ENUM (
    'silicon',
    'germanium',
    'gallium_arsenide'
);

CREATE TYPE device_architecture AS ENUM (
    'gate_defined_quantum_dot',
    'double_quantum_dot',
    'donor_bound_electron'
);

CREATE TYPE device_status AS ENUM (
    'offline',
    'ready',
    'running',
    'fault'
);

CREATE TYPE experiment_status AS ENUM (
    'created',
    'calibrating',
    'approved',
    'running',
    'completed',
    'failed'
);

CREATE TYPE review_decision AS ENUM (
    'pending',
    'approved',
    'rejected'
);

CREATE TYPE pulse_mechanism AS ENUM (
    'esr',
    'edsr',
    'virtual_z'
);

CREATE TYPE measurement_basis AS ENUM (
    'computational',
    'singlet_triplet'
);

-- ------------------------------------------------------------
-- 2. OPERATOR AND ACCESS MANAGEMENT
-- ------------------------------------------------------------

CREATE TABLE operators (
    operator_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(200) NOT NULL,
    role_name VARCHAR(50) NOT NULL CHECK (
        role_name IN (
            'researcher',
            'operator',
            'reviewer',
            'administrator'
        )
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE operator_permissions (
    operator_id BIGINT NOT NULL REFERENCES operators(operator_id),
    permission_name VARCHAR(100) NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (operator_id, permission_name)
);

-- ------------------------------------------------------------
-- 3. SEMICONDUCTOR QUANTUM DEVICES
-- ------------------------------------------------------------

CREATE TABLE quantum_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    device_code VARCHAR(50) NOT NULL UNIQUE,
    material semiconductor_material NOT NULL,
    architecture device_architecture NOT NULL,
    status device_status NOT NULL DEFAULT 'offline',

    electron_count INTEGER NOT NULL CHECK (electron_count > 0),

    temperature_mk NUMERIC(10, 4) NOT NULL
        CHECK (temperature_mk > 0),

    magnetic_field_t NUMERIC(12, 8) NOT NULL
        CHECK (magnetic_field_t >= 0),

    t1_microseconds NUMERIC(14, 6) NOT NULL
        CHECK (t1_microseconds > 0),

    t2_microseconds NUMERIC(14, 6) NOT NULL
        CHECK (
            t2_microseconds > 0
            AND t2_microseconds <= 2 * t1_microseconds
        ),

    exchange_coupling_mhz NUMERIC(14, 6) NOT NULL
        DEFAULT 0 CHECK (exchange_coupling_mhz >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        architecture <> 'double_quantum_dot'
        OR electron_count >= 2
    )
);

CREATE INDEX idx_devices_status
    ON quantum_devices(status);

CREATE INDEX idx_devices_material_architecture
    ON quantum_devices(material, architecture);

-- ------------------------------------------------------------
-- 4. QUBIT REGISTRY
-- ------------------------------------------------------------

CREATE TABLE spin_qubits (
    qubit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    qubit_label VARCHAR(50) NOT NULL,

    bloch_x NUMERIC(12, 9) NOT NULL DEFAULT 0,
    bloch_y NUMERIC(12, 9) NOT NULL DEFAULT 0,
    bloch_z NUMERIC(12, 9) NOT NULL DEFAULT 1,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (device_id, qubit_label),

    CHECK (
        bloch_x * bloch_x +
        bloch_y * bloch_y +
        bloch_z * bloch_z <= 1.0000001
    )
);

CREATE INDEX idx_qubits_device
    ON spin_qubits(device_id);

-- ------------------------------------------------------------
-- 5. EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(60) NOT NULL UNIQUE,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    principal_operator BIGINT NOT NULL
        REFERENCES operators(operator_id),

    experiment_name VARCHAR(200) NOT NULL,

    objective TEXT NOT NULL,

    status experiment_status NOT NULL DEFAULT 'created',

    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        end_time IS NULL
        OR start_time IS NULL
        OR end_time >= start_time
    )
);

CREATE INDEX idx_experiments_device_status
    ON experiments(device_id, status);

CREATE INDEX idx_experiments_created
    ON experiments(created_at DESC);

-- ------------------------------------------------------------
-- 6. EXPERIMENT QUBIT PARTICIPATION
-- ------------------------------------------------------------

CREATE TABLE experiment_qubits (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    qubit_id BIGINT NOT NULL
        REFERENCES spin_qubits(qubit_id),

    role_name VARCHAR(40) NOT NULL DEFAULT 'data',

    PRIMARY KEY (experiment_id, qubit_id)
);

-- ------------------------------------------------------------
-- 7. CALIBRATION RECORDS
-- ------------------------------------------------------------

CREATE TABLE calibrations (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    operator_id BIGINT NOT NULL
        REFERENCES operators(operator_id),

    calibration_code VARCHAR(60) NOT NULL UNIQUE,

    gate_fidelity NUMERIC(8, 7) NOT NULL
        CHECK (gate_fidelity BETWEEN 0 AND 1),

    pi_rotation_rad NUMERIC(12, 8) NOT NULL
        CHECK (pi_rotation_rad > 0),

    magnetic_field_error_t NUMERIC(14, 10) NOT NULL
        CHECK (magnetic_field_error_t >= 0),

    temperature_mk NUMERIC(10, 4) NOT NULL
        CHECK (temperature_mk > 0),

    valid_until TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_calibration_device_validity
    ON calibrations(device_id, valid_until DESC);

CREATE INDEX idx_calibration_fidelity
    ON calibrations(gate_fidelity DESC);

-- ------------------------------------------------------------
-- 8. EXPERIMENT REVIEWS
-- ------------------------------------------------------------

CREATE TABLE experiment_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    reviewer_id BIGINT NOT NULL
        REFERENCES operators(operator_id),

    decision review_decision NOT NULL DEFAULT 'pending',

    review_comment TEXT,

    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (experiment_id, reviewer_id)
);

-- ------------------------------------------------------------
-- 9. CONTROL PULSES
-- ------------------------------------------------------------

CREATE TABLE control_pulses (
    pulse_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL,

    qubit_id BIGINT NOT NULL,

    mechanism pulse_mechanism NOT NULL,

    rotation_axis CHAR(1) NOT NULL
        CHECK (rotation_axis IN ('X', 'Y', 'Z')),

    angle_radians NUMERIC(14, 9) NOT NULL,

    duration_ns NUMERIC(14, 6) NOT NULL
        CHECK (duration_ns > 0),

    drive_frequency_mhz NUMERIC(14, 6)
        CHECK (
            drive_frequency_mhz IS NULL
            OR drive_frequency_mhz > 0
        ),

    amplitude NUMERIC(12, 8)
        CHECK (
            amplitude IS NULL
            OR amplitude BETWEEN 0 AND 1
        ),

    executed_at TIMESTAMPTZ,

    FOREIGN KEY (experiment_id, qubit_id)
        REFERENCES experiment_qubits(experiment_id, qubit_id),

    CHECK (
        mechanism <> 'virtual_z'
        OR rotation_axis = 'Z'
    )
);

CREATE INDEX idx_control_pulses_experiment
    ON control_pulses(experiment_id, executed_at);

CREATE INDEX idx_control_pulses_qubit
    ON control_pulses(qubit_id);

-- ------------------------------------------------------------
-- 10. EXCHANGE INTERACTIONS
-- ------------------------------------------------------------

CREATE TABLE exchange_interactions (
    interaction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    first_qubit_id BIGINT NOT NULL
        REFERENCES spin_qubits(qubit_id),

    second_qubit_id BIGINT NOT NULL
        REFERENCES spin_qubits(qubit_id),

    coupling_mhz NUMERIC(14, 6) NOT NULL
        CHECK (coupling_mhz >= 0),

    duration_us NUMERIC(14, 6) NOT NULL
        CHECK (duration_us > 0),

    relative_phase_rad NUMERIC(16, 9)
        GENERATED ALWAYS AS (
            2 * PI() * coupling_mhz * duration_us
        ) STORED,

    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (first_qubit_id <> second_qubit_id)
);

CREATE INDEX idx_exchange_experiment
    ON exchange_interactions(experiment_id);

-- ------------------------------------------------------------
-- 11. MEASUREMENT RECORDS
-- ------------------------------------------------------------

CREATE TABLE measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    qubit_id BIGINT NOT NULL
        REFERENCES spin_qubits(qubit_id),

    basis measurement_basis NOT NULL DEFAULT 'computational',

    shots INTEGER NOT NULL CHECK (shots > 0),

    zero_count INTEGER NOT NULL DEFAULT 0
        CHECK (zero_count >= 0),

    one_count INTEGER NOT NULL DEFAULT 0
        CHECK (one_count >= 0),

    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (zero_count + one_count = shots)
);

CREATE INDEX idx_measurements_experiment
    ON measurements(experiment_id, measured_at DESC);

CREATE INDEX idx_measurements_qubit
    ON measurements(qubit_id, measured_at DESC);

-- ------------------------------------------------------------
-- 12. DEVICE EVENT AUDIT
-- ------------------------------------------------------------

CREATE TABLE device_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    operator_id BIGINT
        REFERENCES operators(operator_id),

    event_type VARCHAR(100) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_device_time
    ON device_audit(device_id, occurred_at DESC);

CREATE INDEX idx_audit_details
    ON device_audit USING GIN(event_details);

-- ------------------------------------------------------------
-- 13. DATA INTEGRITY TRIGGERS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_qubit_device()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM experiments e
        JOIN spin_qubits q
          ON q.qubit_id = NEW.qubit_id
        WHERE e.experiment_id = NEW.experiment_id
          AND e.device_id = q.device_id
    ) THEN
        RAISE EXCEPTION
            'Experiment and qubit must belong to the same device';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_qubit
BEFORE INSERT OR UPDATE ON experiment_qubits
FOR EACH ROW
EXECUTE FUNCTION validate_qubit_device();


CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'running'
       AND OLD.status <> 'running' THEN

        IF NEW.status <> 'running' THEN
            RAISE EXCEPTION 'Invalid state transition';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM quantum_devices d
            JOIN calibrations c
              ON c.device_id = d.device_id
            WHERE d.device_id = NEW.device_id
              AND d.status = 'ready'
              AND c.valid_until > NOW()
              AND c.gate_fidelity >= 0.95
        ) THEN
            RAISE EXCEPTION
                'No valid device calibration is available';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM experiment_reviews r
            WHERE r.experiment_id = NEW.experiment_id
              AND r.decision = 'approved'
        ) THEN
            RAISE EXCEPTION
                'Experiment requires an approved review';
        END IF;
    END IF;

    IF NEW.status = 'completed'
       AND OLD.status <> 'running' THEN
        RAISE EXCEPTION
            'Only running experiments can be completed';
    END IF;

    IF OLD.status IN ('completed', 'failed')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION
            'Terminal experiment state cannot be changed';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();


CREATE OR REPLACE FUNCTION validate_measurement_experiment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM experiments e
        JOIN experiment_qubits eq
          ON eq.experiment_id = e.experiment_id
         AND eq.qubit_id = NEW.qubit_id
        WHERE e.experiment_id = NEW.experiment_id
          AND e.status = 'running'
    ) THEN
        RAISE EXCEPTION
            'Measurement requires a running experiment and registered qubit';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT ON measurements
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_experiment();


-- ------------------------------------------------------------
-- 14. CALIBRATION ELIGIBILITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION is_device_calibrated(
    p_device_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM calibrations
        WHERE device_id = p_device_id
          AND valid_until > NOW()
          AND gate_fidelity >= 0.95
    );
$$;

-- ------------------------------------------------------------
-- 15. EXPERIMENT ELIGIBILITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION experiment_eligibility(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    experiment_code VARCHAR,
    device_ready BOOLEAN,
    calibration_valid BOOLEAN,
    approval_valid BOOLEAN,
    qubit_registration_valid BOOLEAN,
    eligible BOOLEAN
)
LANGUAGE SQL
STABLE
AS $$
    SELECT
        e.experiment_code,

        d.status = 'ready',

        is_device_calibrated(e.device_id),

        EXISTS (
            SELECT 1
            FROM experiment_reviews r
            WHERE r.experiment_id = e.experiment_id
              AND r.decision = 'approved'
        ),

        EXISTS (
            SELECT 1
            FROM experiment_qubits eq
            WHERE eq.experiment_id = e.experiment_id
        ),

        (
            d.status = 'ready'
            AND is_device_calibrated(e.device_id)
            AND EXISTS (
                SELECT 1
                FROM experiment_reviews r
                WHERE r.experiment_id = e.experiment_id
                  AND r.decision = 'approved'
            )
            AND EXISTS (
                SELECT 1
                FROM experiment_qubits eq
                WHERE eq.experiment_id = e.experiment_id
            )
        )

    FROM experiments e
    JOIN quantum_devices d
      ON d.device_id = e.device_id

    WHERE e.experiment_id = p_experiment_id;
$$;

-- ------------------------------------------------------------
-- 16. REPORTING VIEWS
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW device_performance_report AS
SELECT
    d.device_code,
    d.material,
    d.architecture,
    d.temperature_mk,
    d.magnetic_field_t,
    d.t1_microseconds,
    d.t2_microseconds,
    d.exchange_coupling_mhz,
    COUNT(DISTINCT q.qubit_id) AS registered_qubits,
    COUNT(DISTINCT e.experiment_id) AS total_experiments,
    ROUND(
        AVG(c.gate_fidelity)::NUMERIC,
        7
    ) AS average_calibration_fidelity

FROM quantum_devices d

LEFT JOIN spin_qubits q
    ON q.device_id = d.device_id

LEFT JOIN experiments e
    ON e.device_id = d.device_id

LEFT JOIN calibrations c
    ON c.device_id = d.device_id

GROUP BY d.device_id;


CREATE OR REPLACE VIEW measurement_statistics AS
SELECT
    e.experiment_code,
    q.qubit_label,
    COUNT(m.measurement_id) AS measurement_count,
    COALESCE(SUM(m.shots), 0) AS total_shots,
    COALESCE(SUM(m.zero_count), 0) AS total_zero,
    COALESCE(SUM(m.one_count), 0) AS total_one,

    ROUND(
        SUM(m.zero_count)::NUMERIC /
        NULLIF(SUM(m.shots), 0),
        6
    ) AS probability_zero

FROM experiments e

JOIN experiment_qubits eq
    ON eq.experiment_id = e.experiment_id

JOIN spin_qubits q
    ON q.qubit_id = eq.qubit_id

LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
   AND m.qubit_id = q.qubit_id

GROUP BY e.experiment_code, q.qubit_label;


CREATE OR REPLACE VIEW coherence_report AS
SELECT
    device_code,
    material,
    t1_microseconds,
    t2_microseconds,
    ROUND(
        t2_microseconds / NULLIF(t1_microseconds, 0),
        6
    ) AS t2_to_t1_ratio,
    CASE
        WHEN t2_microseconds < 10 THEN 'LOW_COHERENCE'
        WHEN t2_microseconds < 100 THEN 'MODERATE_COHERENCE'
        ELSE 'HIGH_COHERENCE'
    END AS coherence_category
FROM quantum_devices;

-- ------------------------------------------------------------
-- 17. SAMPLE RECORDS
-- ------------------------------------------------------------

INSERT INTO operators(username, full_name, role_name)
VALUES
    ('researcher01', 'Quantum Researcher', 'researcher'),
    ('operator01', 'Device Operator', 'operator'),
    ('reviewer01', 'Principal Investigator', 'reviewer'),
    ('admin01', 'Laboratory Administrator', 'administrator');

INSERT INTO operator_permissions(operator_id, permission_name)
SELECT operator_id, 'RUN_EXPERIMENT'
FROM operators
WHERE username = 'operator01';

INSERT INTO operator_permissions(operator_id, permission_name)
SELECT operator_id, 'REVIEW_EXPERIMENT'
FROM operators
WHERE username = 'reviewer01';

INSERT INTO quantum_devices (
    device_code,
    material,
    architecture,
    status,
    electron_count,
    temperature_mk,
    magnetic_field_t,
    t1_microseconds,
    t2_microseconds,
    exchange_coupling_mhz
)
VALUES
(
    'SI-QD-001',
    'silicon',
    'double_quantum_dot',
    'ready',
    2,
    20,
    0.5,
    1000,
    100,
    5
),
(
    'GE-QD-002',
    'germanium',
    'gate_defined_quantum_dot',
    'offline',
    1,
    15,
    0.7,
    800,
    80,
    2
),
(
    'GAAS-QD-003',
    'gallium_arsenide',
    'double_quantum_dot',
    'fault',
    2,
    25,
    0.4,
    500,
    50,
    3
);

INSERT INTO spin_qubits(device_id, qubit_label)
SELECT device_id, 'Q0'
FROM quantum_devices
WHERE device_code = 'SI-QD-001';

INSERT INTO spin_qubits(device_id, qubit_label)
SELECT device_id, 'Q1'
FROM quantum_devices
WHERE device_code = 'SI-QD-001';

INSERT INTO spin_qubits(device_id, qubit_label)
SELECT device_id, 'Q0'
FROM quantum_devices
WHERE device_code = 'GE-QD-002';

INSERT INTO experiments (
    experiment_code,
    device_id,
    principal_operator,
    experiment_name,
    objective,
    status
)
SELECT
    'SPIN-EXP-001',
    d.device_id,
    o.operator_id,
    'Electron spin coherence characterization',
    'Measure spin relaxation and dephasing behavior.',
    'calibrating'
FROM quantum_devices d
CROSS JOIN operators o
WHERE d.device_code = 'SI-QD-001'
  AND o.username = 'operator01';

INSERT INTO experiments (
    experiment_code,
    device_id,
    principal_operator,
    experiment_name,
    objective,
    status
)
SELECT
    'SPIN-EXP-002',
    d.device_id,
    o.operator_id,
    'Germanium spin initialization study',
    'Evaluate initialization readiness.',
    'created'
FROM quantum_devices d
CROSS JOIN operators o
WHERE d.device_code = 'GE-QD-002'
  AND o.username = 'researcher01';

INSERT INTO experiment_qubits(experiment_id, qubit_id, role_name)
SELECT e.experiment_id, q.qubit_id, 'control'
FROM experiments e
JOIN quantum_devices d
    ON d.device_id = e.device_id
JOIN spin_qubits q
    ON q.device_id = d.device_id
WHERE e.experiment_code = 'SPIN-EXP-001';

INSERT INTO experiment_qubits(experiment_id, qubit_id, role_name)
SELECT e.experiment_id, q.qubit_id, 'data'
FROM experiments e
JOIN quantum_devices d
    ON d.device_id = e.device_id
JOIN spin_qubits q
    ON q.device_id = d.device_id
WHERE e.experiment_code = 'SPIN-EXP-002'
  AND q.qubit_label = 'Q0';

INSERT INTO calibrations (
    device_id,
    operator_id,
    calibration_code,
    gate_fidelity,
    pi_rotation_rad,
    magnetic_field_error_t,
    temperature_mk,
    valid_until
)
SELECT
    d.device_id,
    o.operator_id,
    'CAL-SI-001',
    0.995,
    PI(),
    0.0001,
    20,
    NOW() + INTERVAL '30 days'
FROM quantum_devices d
CROSS JOIN operators o
WHERE d.device_code = 'SI-QD-001'
  AND o.username = 'operator01';

INSERT INTO calibrations (
    device_id,
    operator_id,
    calibration_code,
    gate_fidelity,
    pi_rotation_rad,
    magnetic_field_error_t,
    temperature_mk,
    valid_until
)
SELECT
    d.device_id,
    o.operator_id,
    'CAL-GE-001',
    0.91,
    PI(),
    0.001,
    15,
    NOW() + INTERVAL '30 days'
FROM quantum_devices d
CROSS JOIN operators o
WHERE d.device_code = 'GE-QD-002'
  AND o.username = 'operator01';

INSERT INTO experiment_reviews (
    experiment_id,
    reviewer_id,
    decision,
    review_comment
)
SELECT
    e.experiment_id,
    o.operator_id,
    'approved',
    'Device calibration and experiment configuration verified.'
FROM experiments e
CROSS JOIN operators o
WHERE e.experiment_code = 'SPIN-EXP-001'
  AND o.username = 'reviewer01';

INSERT INTO experiment_reviews (
    experiment_id,
    reviewer_id,
    decision,
    review_comment
)
SELECT
    e.experiment_id,
    o.operator_id,
    'rejected',
    'Calibration fidelity is below the experiment threshold.'
FROM experiments e
CROSS JOIN operators o
WHERE e.experiment_code = 'SPIN-EXP-002'
  AND o.username = 'reviewer01';

-- ------------------------------------------------------------
-- 18. TRANSACTIONAL EXPERIMENT EXECUTION
-- ------------------------------------------------------------

DO $$
DECLARE
    v_experiment_id BIGINT;
    v_device_id BIGINT;
    v_operator_id BIGINT;
BEGIN
    SELECT experiment_id, device_id
    INTO v_experiment_id, v_device_id
    FROM experiments
    WHERE experiment_code = 'SPIN-EXP-001';

    SELECT operator_id
    INTO v_operator_id
    FROM operators
    WHERE username = 'operator01';

    -- The experiment is started only after eligibility is verified.
    IF NOT is_device_calibrated(v_device_id) THEN
        RAISE EXCEPTION 'Device calibration is not valid';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM experiment_reviews
        WHERE experiment_id = v_experiment_id
          AND decision = 'approved'
    ) THEN
        RAISE EXCEPTION 'Experiment approval is missing';
    END IF;

    UPDATE quantum_devices
    SET status = 'running'
    WHERE device_id = v_device_id
      AND status = 'ready';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Device is not ready';
    END IF;

    UPDATE experiments
    SET status = 'running',
        start_time = NOW()
    WHERE experiment_id = v_experiment_id
      AND status = 'calibrating';

    INSERT INTO device_audit (
        device_id,
        operator_id,
        event_type,
        event_details
    )
    VALUES (
        v_device_id,
        v_operator_id,
        'EXPERIMENT_STARTED',
        jsonb_build_object(
            'experiment_id', v_experiment_id,
            'experiment_code', 'SPIN-EXP-001'
        )
    );

    -- Demonstration of ESR control pulse.
    INSERT INTO control_pulses (
        experiment_id,
        qubit_id,
        mechanism,
        rotation_axis,
        angle_radians,
        duration_ns,
        drive_frequency_mhz,
        amplitude,
        executed_at
    )
    SELECT
        v_experiment_id,
        q.qubit_id,
        'esr',
        'Y',
        PI() / 2,
        50,
        28000,
        0.5,
        NOW()
    FROM experiment_qubits eq
    JOIN spin_qubits q
        ON q.qubit_id = eq.qubit_id
    WHERE eq.experiment_id = v_experiment_id
      AND q.qubit_label = 'Q0';

    -- Demonstration of computational-basis measurement.
    INSERT INTO measurements (
        experiment_id,
        qubit_id,
        basis,
        shots,
        zero_count,
        one_count
    )
    SELECT
        v_experiment_id,
        q.qubit_id,
        'computational',
        1000,
        510,
        490
    FROM experiment_qubits eq
    JOIN spin_qubits q
        ON q.qubit_id = eq.qubit_id
    WHERE eq.experiment_id = v_experiment_id
      AND q.qubit_label = 'Q0';

    -- Two-qubit exchange interaction.
    INSERT INTO exchange_interactions (
        experiment_id,
        first_qubit_id,
        second_qubit_id,
        coupling_mhz,
        duration_us
    )
    SELECT
        v_experiment_id,
        q1.qubit_id,
        q2.qubit_id,
        5,
        0.05
    FROM spin_qubits q1
    JOIN spin_qubits q2
        ON q1.device_id = q2.device_id
    WHERE q1.qubit_label = 'Q0'
      AND q2.qubit_label = 'Q1'
      AND q1.device_id = v_device_id;

    UPDATE experiments
    SET status = 'completed',
        end_time = NOW()
    WHERE experiment_id = v_experiment_id;

    UPDATE quantum_devices
    SET status = 'ready'
    WHERE device_id = v_device_id;

    INSERT INTO device_audit (
        device_id,
        operator_id,
        event_type,
        event_details
    )
    VALUES (
        v_device_id,
        v_operator_id,
        'EXPERIMENT_COMPLETED',
        jsonb_build_object(
            'experiment_id', v_experiment_id
        )
    );
END;
$$;

COMMIT;

-- ------------------------------------------------------------
-- 19. RETRIEVAL QUERIES
-- ------------------------------------------------------------

-- List devices with their operating conditions.
SELECT
    device_code,
    material,
    architecture,
    status,
    temperature_mk,
    magnetic_field_t,
    t1_microseconds,
    t2_microseconds
FROM quantum_devices
ORDER BY device_code;

-- Retrieve qubits registered with each device.
SELECT
    d.device_code,
    q.qubit_label,
    q.bloch_x,
    q.bloch_y,
    q.bloch_z,
    q.enabled
FROM spin_qubits q
JOIN quantum_devices d
    ON d.device_id = q.device_id
ORDER BY d.device_code, q.qubit_label;

-- ------------------------------------------------------------
-- 20. VALIDATION AND ELIGIBILITY QUERIES
-- ------------------------------------------------------------

SELECT
    d.device_code,
    is_device_calibrated(d.device_id) AS calibration_valid
FROM quantum_devices d;

SELECT *
FROM experiment_eligibility(
    (SELECT experiment_id
     FROM experiments
     WHERE experiment_code = 'SPIN-EXP-001')
);

SELECT
    e.experiment_code,
    e.status,
    d.status AS device_status,
    CASE
        WHEN d.status <> 'ready' THEN 'DEVICE_NOT_READY'
        WHEN NOT is_device_calibrated(d.device_id)
            THEN 'CALIBRATION_INVALID'
        WHEN NOT EXISTS (
            SELECT 1
            FROM experiment_reviews r
            WHERE r.experiment_id = e.experiment_id
              AND r.decision = 'approved'
        ) THEN 'APPROVAL_MISSING'
        WHEN NOT EXISTS (
            SELECT 1
            FROM experiment_qubits eq
            WHERE eq.experiment_id = e.experiment_id
        ) THEN 'NO_REGISTERED_QUBITS'
        ELSE 'ELIGIBLE'
    END AS eligibility_reason
FROM experiments e
JOIN quantum_devices d
    ON d.device_id = e.device_id;

-- ------------------------------------------------------------
-- 21. AGGREGATION AND REPORTING
-- ------------------------------------------------------------

SELECT *
FROM device_performance_report
ORDER BY device_code;

SELECT *
FROM coherence_report
ORDER BY t2_microseconds DESC;

SELECT *
FROM measurement_statistics
ORDER BY experiment_code, qubit_label;

-- Average measurement probability by experiment.
SELECT
    experiment_code,
    SUM(total_shots) AS shots,
    ROUND(
        SUM(total_zero)::NUMERIC /
        NULLIF(SUM(total_shots), 0),
        6
    ) AS aggregate_probability_zero
FROM measurement_statistics
GROUP BY experiment_code;

-- Exchange interaction reporting.
SELECT
    e.experiment_code,
    q1.qubit_label AS first_qubit,
    q2.qubit_label AS second_qubit,
    x.coupling_mhz,
    x.duration_us,
    x.relative_phase_rad
FROM exchange_interactions x
JOIN experiments e
    ON e.experiment_id = x.experiment_id
JOIN spin_qubits q1
    ON q1.qubit_id = x.first_qubit_id
JOIN spin_qubits q2
    ON q2.qubit_id = x.second_qubit_id;

-- ------------------------------------------------------------
-- 22. CTE: DEVICE CALIBRATION RANKING
-- ------------------------------------------------------------

WITH calibration_ranking AS (
    SELECT
        d.device_code,
        c.calibration_code,
        c.gate_fidelity,
        c.valid_until,
        ROW_NUMBER() OVER (
            PARTITION BY d.device_id
            ORDER BY c.gate_fidelity DESC, c.created_at DESC
        ) AS ranking
    FROM quantum_devices d
    JOIN calibrations c
        ON c.device_id = d.device_id
)
SELECT
    device_code,
    calibration_code,
    gate_fidelity,
    valid_until
FROM calibration_ranking
WHERE ranking = 1;

-- ------------------------------------------------------------
-- 23. AUDIT RETRIEVAL
-- ------------------------------------------------------------

SELECT
    d.device_code,
    a.event_type,
    a.event_details,
    a.occurred_at
FROM device_audit a
JOIN quantum_devices d
    ON d.device_id = a.device_id
ORDER BY a.occurred_at DESC;

-- ------------------------------------------------------------
-- 24. FAILURE CASE QUERIES
-- ------------------------------------------------------------

-- Devices whose calibration is expired or below threshold.
SELECT
    d.device_code,
    c.calibration_code,
    c.gate_fidelity,
    c.valid_until
FROM quantum_devices d
JOIN calibrations c
    ON c.device_id = d.device_id
WHERE c.gate_fidelity < 0.95
   OR c.valid_until <= NOW();

-- Experiments requiring approval.
SELECT
    e.experiment_code,
    e.status,
    r.decision,
    r.review_comment
FROM experiments e
LEFT JOIN experiment_reviews r
    ON r.experiment_id = e.experiment_id
WHERE e.status IN ('created', 'calibrating')
  AND (
      r.decision IS NULL
      OR r.decision <> 'approved'
  );

-- ------------------------------------------------------------
-- 25. PERFORMANCE NOTES
-- ------------------------------------------------------------

-- Composite indexes support device/experiment lookup.
-- Time-series indexes support chronological measurement retrieval.
-- GIN supports JSONB audit-detail filtering.
-- Large experimental measurement datasets should be partitioned
-- by measured_at using monthly or quarterly range partitions.
-- Database access should use separate least-privilege roles.
-- Sensitive experimental metadata should be protected by
-- PostgreSQL privileges, row-level security, and audit controls.
