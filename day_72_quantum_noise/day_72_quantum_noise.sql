-- ============================================================
-- QUANTUM NOISE CHARACTERIZATION DATABASE
-- PostgreSQL 15+
--
-- Models:
-- 1. Quantum devices and qubits
-- 2. Noise sources and channel models
-- 3. T1/T2 coherence calibration
-- 4. Noise experiments
-- 5. Applied noise channels
-- 6. Measurement readout errors
-- 7. Experimental observations
-- 8. Quality evaluation and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_noise;

SET search_path TO quantum_noise, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE noise_category AS ENUM (
    'RELAXATION',
    'DEPHASING',
    'DEPOLARIZATION',
    'BIT_FLIP',
    'PHASE_FLIP',
    'COHERENT',
    'THERMAL',
    'READOUT'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE experiment_outcome AS ENUM (
    'PASS',
    'WARNING',
    'FAIL'
);

CREATE TYPE device_status AS ENUM (
    'ACTIVE',
    'MAINTENANCE',
    'RETIRED'
);

-- ------------------------------------------------------------
-- 2. QUANTUM DEVICES
-- ------------------------------------------------------------

CREATE TABLE quantum_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_name VARCHAR(120) NOT NULL UNIQUE,

    technology VARCHAR(60) NOT NULL,

    manufacturer VARCHAR(120),

    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),

    operating_temperature_kelvin NUMERIC(12, 8)
        CHECK (
            operating_temperature_kelvin IS NULL
            OR operating_temperature_kelvin > 0
        ),

    status device_status NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. QUBITS
-- ------------------------------------------------------------

CREATE TABLE quantum_qubits (
    qubit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    physical_index INTEGER NOT NULL CHECK (physical_index >= 0),

    t1_seconds DOUBLE PRECISION
        CHECK (t1_seconds IS NULL OR t1_seconds > 0),

    t2_seconds DOUBLE PRECISION
        CHECK (t2_seconds IS NULL OR t2_seconds > 0),

    frequency_hz DOUBLE PRECISION
        CHECK (frequency_hz IS NULL OR frequency_hz > 0),

    last_calibrated_at TIMESTAMPTZ,

    UNIQUE(device_id, physical_index),

    CHECK (
        t1_seconds IS NULL
        OR t2_seconds IS NULL
        OR t2_seconds <= 2 * t1_seconds
    )
);

CREATE INDEX idx_qubits_device
ON quantum_qubits(device_id);

-- ------------------------------------------------------------
-- 4. NOISE SOURCE CATALOG
-- ------------------------------------------------------------

CREATE TABLE noise_sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_name VARCHAR(120) NOT NULL UNIQUE,

    category noise_category NOT NULL,

    physical_mechanism TEXT NOT NULL,

    affected_property VARCHAR(80) NOT NULL,

    stochastic BOOLEAN NOT NULL DEFAULT TRUE,

    description TEXT
);

INSERT INTO noise_sources (
    source_name,
    category,
    physical_mechanism,
    affected_property,
    stochastic,
    description
)
VALUES
(
    'Energy relaxation',
    'RELAXATION',
    'Energy exchange between qubit and environment',
    'Excited-state population',
    TRUE,
    'T1-related decay from excited to ground state.'
),
(
    'Pure dephasing',
    'DEPHASING',
    'Random environmental phase accumulation',
    'Off-diagonal density matrix elements',
    TRUE,
    'Reduces quantum coherence without directly changing populations.'
),
(
    'Depolarizing noise',
    'DEPOLARIZATION',
    'Random Pauli error events',
    'Bloch-vector polarization',
    TRUE,
    'Effective model for isotropic random Pauli errors.'
),
(
    'Bit-flip noise',
    'BIT_FLIP',
    'Random Pauli X operation',
    'Computational-basis information',
    TRUE,
    'Models probabilistic bit inversion.'
),
(
    'Phase-flip noise',
    'PHASE_FLIP',
    'Random Pauli Z operation',
    'Relative phase',
    TRUE,
    'Models probabilistic phase inversion.'
),
(
    'Coherent control error',
    'COHERENT',
    'Systematic control-angle miscalibration',
    'Quantum phase and gate rotation',
    FALSE,
    'Models deterministic unitary rotation error.'
),
(
    'Thermal excitation',
    'THERMAL',
    'Thermal population exchange with environment',
    'Equilibrium state population',
    TRUE,
    'Generalized amplitude damping with nonzero excited-state population.'
),
(
    'Measurement readout error',
    'READOUT',
    'Incorrect classical outcome reporting',
    'Measured bit value',
    TRUE,
    'Models measurement assignment errors.'
);

-- ------------------------------------------------------------
-- 5. NOISE CHANNEL MODELS
-- ------------------------------------------------------------

CREATE TABLE noise_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_name VARCHAR(120) NOT NULL UNIQUE,

    category noise_category NOT NULL,

    parameter_name VARCHAR(80) NOT NULL,

    minimum_parameter DOUBLE PRECISION NOT NULL,

    maximum_parameter DOUBLE PRECISION NOT NULL,

    mathematical_description TEXT NOT NULL,

    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (minimum_parameter <= maximum_parameter)
);

INSERT INTO noise_models (
    model_name,
    category,
    parameter_name,
    minimum_parameter,
    maximum_parameter,
    mathematical_description
)
VALUES
(
    'Amplitude Damping',
    'RELAXATION',
    'gamma',
    0,
    1,
    'Population transition probability gamma.'
),
(
    'Pure Dephasing',
    'DEPHASING',
    'probability',
    0,
    0.5,
    'Coherence scaling factor 1 - 2p.'
),
(
    'Depolarizing',
    'DEPOLARIZATION',
    'probability',
    0,
    1,
    'Pauli channel with equal X, Y and Z probabilities p/3.'
),
(
    'Bit Flip',
    'BIT_FLIP',
    'probability',
    0,
    1,
    'Identity with probability 1-p and X with probability p.'
),
(
    'Phase Flip',
    'PHASE_FLIP',
    'probability',
    0,
    1,
    'Identity with probability 1-p and Z with probability p.'
),
(
    'Coherent Z Rotation',
    'COHERENT',
    'angle_radians',
    -6.283185307179586,
    6.283185307179586,
    'Unitary Z rotation with deterministic angle error.'
),
(
    'Thermal Relaxation',
    'THERMAL',
    'gamma',
    0,
    1,
    'Generalized amplitude damping with an equilibrium excited-state population.'
),
(
    'Readout Confusion',
    'READOUT',
    'probability',
    0,
    1,
    'Classical measurement assignment error.'
);

-- ------------------------------------------------------------
-- 6. COHERENCE CALIBRATION
-- ------------------------------------------------------------

CREATE TABLE coherence_calibrations (
    calibration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    qubit_id BIGINT NOT NULL
        REFERENCES quantum_qubits(qubit_id),

    t1_seconds DOUBLE PRECISION NOT NULL CHECK (t1_seconds > 0),

    t2_seconds DOUBLE PRECISION NOT NULL CHECK (
        t2_seconds > 0 AND t2_seconds <= 2 * t1_seconds
    ),

    pure_dephasing_time_seconds DOUBLE PRECISION,

    calibration_temperature_kelvin DOUBLE PRECISION
        CHECK (
            calibration_temperature_kelvin IS NULL
            OR calibration_temperature_kelvin > 0
        ),

    calibration_method VARCHAR(100) NOT NULL,

    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    calibrated_by VARCHAR(120) NOT NULL,

    CHECK (
        pure_dephasing_time_seconds IS NULL
        OR pure_dephasing_time_seconds > 0
    )
);

CREATE INDEX idx_calibration_qubit_date
ON coherence_calibrations(qubit_id, calibrated_at DESC);

-- ------------------------------------------------------------
-- 7. EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE noise_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(100) NOT NULL UNIQUE,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    qubit_id BIGINT NOT NULL
        REFERENCES quantum_qubits(qubit_id),

    calibration_id BIGINT
        REFERENCES coherence_calibrations(calibration_id),

    experiment_name VARCHAR(160) NOT NULL,

    initial_state_x DOUBLE PRECISION NOT NULL DEFAULT 0,

    initial_state_y DOUBLE PRECISION NOT NULL DEFAULT 0,

    initial_state_z DOUBLE PRECISION NOT NULL DEFAULT 1,

    duration_seconds DOUBLE PRECISION NOT NULL DEFAULT 0
        CHECK (duration_seconds >= 0),

    shots INTEGER NOT NULL DEFAULT 1000 CHECK (shots > 0),

    status experiment_status NOT NULL DEFAULT 'CREATED',

    outcome experiment_outcome,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_by VARCHAR(120) NOT NULL,

    CHECK (
        initial_state_x * initial_state_x
        + initial_state_y * initial_state_y
        + initial_state_z * initial_state_z
        <= 1.000000001
    ),

    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE INDEX idx_experiment_status
ON noise_experiments(status, created_at DESC);

CREATE INDEX idx_experiment_device
ON noise_experiments(device_id, created_at DESC);

-- ------------------------------------------------------------
-- 8. APPLIED NOISE CHANNELS
-- ------------------------------------------------------------

CREATE TABLE experiment_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES noise_experiments(experiment_id)
        ON DELETE CASCADE,

    model_id BIGINT NOT NULL
        REFERENCES noise_models(model_id),

    sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),

    parameter_value DOUBLE PRECISION NOT NULL,

    excited_population DOUBLE PRECISION
        CHECK (
            excited_population IS NULL
            OR excited_population BETWEEN 0 AND 1
        ),

    description TEXT,

    UNIQUE(experiment_id, sequence_number),

    CHECK (
        parameter_value BETWEEN -6.283185307179586
        AND 6.283185307179586
    )
);

CREATE INDEX idx_channels_experiment
ON experiment_channels(experiment_id, sequence_number);

-- ------------------------------------------------------------
-- 9. READOUT CALIBRATION
-- ------------------------------------------------------------

CREATE TABLE readout_calibrations (
    readout_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    qubit_id BIGINT NOT NULL
        REFERENCES quantum_qubits(qubit_id),

    p_zero_to_one DOUBLE PRECISION NOT NULL
        CHECK (p_zero_to_one BETWEEN 0 AND 1),

    p_one_to_zero DOUBLE PRECISION NOT NULL
        CHECK (p_one_to_zero BETWEEN 0 AND 1),

    calibration_shots INTEGER NOT NULL CHECK (calibration_shots > 0),

    calibrated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    calibrated_by VARCHAR(120) NOT NULL
);

-- ------------------------------------------------------------
-- 10. EXPERIMENT OBSERVATIONS
-- ------------------------------------------------------------

CREATE TABLE noise_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES noise_experiments(experiment_id)
        ON DELETE CASCADE,

    observation_type VARCHAR(80) NOT NULL,

    observed_x DOUBLE PRECISION,

    observed_y DOUBLE PRECISION,

    observed_z DOUBLE PRECISION,

    measured_zero INTEGER CHECK (measured_zero >= 0),

    measured_one INTEGER CHECK (measured_one >= 0),

    estimated_fidelity DOUBLE PRECISION
        CHECK (
            estimated_fidelity IS NULL
            OR estimated_fidelity BETWEEN 0 AND 1
        ),

    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        observed_x IS NULL
        OR observed_y IS NULL
        OR observed_z IS NULL
        OR (
            observed_x * observed_x
            + observed_y * observed_y
            + observed_z * observed_z
            <= 1.000000001
        )
    ),

    CHECK (
        measured_zero IS NULL
        OR measured_one IS NULL
        OR measured_zero + measured_one > 0
    )
);

CREATE INDEX idx_observations_experiment
ON noise_observations(experiment_id, observed_at DESC);

-- ------------------------------------------------------------
-- 11. AUTOMATIC EXPERIMENT VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    actual_device_id BIGINT;
    actual_qubit_id BIGINT;
BEGIN
    SELECT device_id
    INTO actual_device_id
    FROM quantum_qubits
    WHERE qubit_id = NEW.qubit_id;

    IF actual_qubit_id IS NULL AND NOT FOUND THEN
        RAISE EXCEPTION 'Referenced qubit does not exist';
    END IF;

    IF actual_device_id <> NEW.device_id THEN
        RAISE EXCEPTION
            'Qubit does not belong to the selected device';
    END IF;

    IF NEW.calibration_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM coherence_calibrations c
            WHERE c.calibration_id = NEW.calibration_id
              AND c.qubit_id = NEW.qubit_id
        ) THEN
            RAISE EXCEPTION
                'Calibration does not belong to the experiment qubit';
        END IF;
    END IF;

    IF NEW.status IN ('RUNNING', 'COMPLETED') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM experiment_channels ec
            WHERE ec.experiment_id = NEW.experiment_id
        ) AND TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION
                'At least one noise channel is required';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment
BEFORE INSERT OR UPDATE
ON noise_experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_configuration();

-- ------------------------------------------------------------
-- 12. CHANNEL PARAMETER VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_channel_parameter()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    minimum_value DOUBLE PRECISION;
    maximum_value DOUBLE PRECISION;
    selected_model VARCHAR(120);
BEGIN
    SELECT
        minimum_parameter,
        maximum_parameter,
        model_name
    INTO
        minimum_value,
        maximum_value,
        selected_model
    FROM noise_models
    WHERE model_id = NEW.model_id
      AND is_enabled = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Noise model is missing or disabled';
    END IF;

    IF NEW.parameter_value < minimum_value
       OR NEW.parameter_value > maximum_value THEN
        RAISE EXCEPTION
            'Parameter outside permitted range for model %',
            selected_model;
    END IF;

    IF selected_model = 'Pure Dephasing'
       AND NEW.parameter_value > 0.5 THEN
        RAISE EXCEPTION
            'Pure dephasing probability cannot exceed 0.5';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_channel
BEFORE INSERT OR UPDATE
ON experiment_channels
FOR EACH ROW
EXECUTE FUNCTION validate_channel_parameter();

-- ------------------------------------------------------------
-- 13. EXPERIMENT LIFECYCLE
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_experiment_status(
    p_experiment_id BIGINT,
    p_new_status experiment_status,
    p_outcome experiment_outcome DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM noise_experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found';
    END IF;

    IF current_status = 'COMPLETED'
       OR current_status = 'FAILED'
       OR current_status = 'CANCELLED' THEN
        RAISE EXCEPTION 'Terminal experiment state cannot transition';
    END IF;

    IF p_new_status = 'RUNNING'
       AND current_status <> 'VALIDATED' THEN
        RAISE EXCEPTION 'Experiment must be validated before execution';
    END IF;

    IF p_new_status = 'COMPLETED'
       AND current_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only running experiments can complete';
    END IF;

    IF p_new_status = 'COMPLETED'
       AND p_outcome IS NULL THEN
        RAISE EXCEPTION 'Completed experiments require an outcome';
    END IF;

    UPDATE noise_experiments
    SET
        status = p_new_status,
        outcome = p_outcome,
        started_at = CASE
            WHEN p_new_status = 'RUNNING'
            THEN COALESCE(started_at, CURRENT_TIMESTAMP)
            ELSE started_at
        END,
        completed_at = CASE
            WHEN p_new_status IN ('COMPLETED', 'FAILED', 'CANCELLED')
            THEN CURRENT_TIMESTAMP
            ELSE completed_at
        END
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- 14. EXPERIMENT CHANNEL VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_experiment_noise_channels AS
SELECT
    e.experiment_code,
    e.experiment_name,
    e.status,
    d.device_name,
    q.physical_index,
    ns.category,
    nm.model_name,
    ec.sequence_number,
    ec.parameter_value,
    ec.excited_population
FROM noise_experiments e
JOIN quantum_devices d
    ON d.device_id = e.device_id
JOIN quantum_qubits q
    ON q.qubit_id = e.qubit_id
JOIN experiment_channels ec
    ON ec.experiment_id = e.experiment_id
JOIN noise_models nm
    ON nm.model_id = ec.model_id
JOIN noise_sources ns
    ON ns.category = nm.category;

-- ------------------------------------------------------------
-- 15. COHERENCE CALIBRATION REPORT
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_coherence_report AS
SELECT
    d.device_name,
    q.physical_index,
    c.t1_seconds,
    c.t2_seconds,
    CASE
        WHEN c.t2_seconds = 2 * c.t1_seconds
        THEN NULL
        ELSE 1.0 / (
            1.0 / c.t2_seconds
            - 1.0 / (2.0 * c.t1_seconds)
        )
    END AS pure_dephasing_time_seconds,
    c.calibrated_at,
    c.calibrated_by
FROM coherence_calibrations c
JOIN quantum_qubits q
    ON q.qubit_id = c.qubit_id
JOIN quantum_devices d
    ON d.device_id = q.device_id;

-- ------------------------------------------------------------
-- 16. EXPERIMENT PERFORMANCE AGGREGATION
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_experiment_quality AS
SELECT
    e.experiment_id,
    e.experiment_code,
    e.experiment_name,
    e.status,
    e.outcome,
    COUNT(o.observation_id) AS observation_count,
    AVG(o.estimated_fidelity) AS average_fidelity,
    AVG(
        CASE
            WHEN o.measured_zero IS NOT NULL
                 AND o.measured_one IS NOT NULL
            THEN o.measured_zero::DOUBLE PRECISION
                 / NULLIF(
                     o.measured_zero + o.measured_one,
                     0
                 )
        END
    ) AS average_zero_frequency
FROM noise_experiments e
LEFT JOIN noise_observations o
    ON o.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_code,
    e.experiment_name,
    e.status,
    e.outcome;

-- ------------------------------------------------------------
-- 17. SAMPLE DEVICE AND QUBIT DATA
-- ------------------------------------------------------------

INSERT INTO quantum_devices (
    device_name,
    technology,
    manufacturer,
    qubit_count,
    operating_temperature_kelvin
)
VALUES
(
    'QPU-ALPHA',
    'Superconducting',
    'Quantum Systems Laboratory',
    5,
    0.015
),
(
    'QPU-BETA',
    'Trapped Ion',
    'Quantum Research Laboratory',
    4,
    0.001
);

INSERT INTO quantum_qubits (
    device_id,
    physical_index,
    t1_seconds,
    t2_seconds,
    frequency_hz
)
SELECT
    device_id,
    physical_index,
    100e-6,
    70e-6,
    5.0e9
FROM quantum_devices
CROSS JOIN generate_series(0, 1) AS physical_index
WHERE device_name = 'QPU-ALPHA';

-- ------------------------------------------------------------
-- 18. SAMPLE COHERENCE CALIBRATION
-- ------------------------------------------------------------

INSERT INTO coherence_calibrations (
    qubit_id,
    t1_seconds,
    t2_seconds,
    calibration_method,
    calibrated_by
)
SELECT
    q.qubit_id,
    100e-6,
    70e-6,
    'Relaxation and Ramsey measurements',
    'research-engineer'
FROM quantum_qubits q
JOIN quantum_devices d
    ON d.device_id = q.device_id
WHERE d.device_name = 'QPU-ALPHA'
AND q.physical_index = 0;

-- ------------------------------------------------------------
-- 19. SAMPLE EXPERIMENT
-- ------------------------------------------------------------

INSERT INTO noise_experiments (
    experiment_code,
    device_id,
    qubit_id,
    calibration_id,
    experiment_name,
    initial_state_x,
    initial_state_y,
    initial_state_z,
    duration_seconds,
    shots,
    created_by
)
SELECT
    'QN-EXP-001',
    d.device_id,
    q.qubit_id,
    c.calibration_id,
    'Single-Qubit Noise Characterization',
    1.0,
    0.0,
    0.0,
    20e-6,
    10000,
    'research-engineer'
FROM quantum_devices d
JOIN quantum_qubits q
    ON q.device_id = d.device_id
JOIN coherence_calibrations c
    ON c.qubit_id = q.qubit_id
WHERE d.device_name = 'QPU-ALPHA'
AND q.physical_index = 0
AND c.calibrated_by = 'research-engineer';

-- ------------------------------------------------------------
-- 20. REGISTER NOISE CHANNELS
-- ------------------------------------------------------------

INSERT INTO experiment_channels (
    experiment_id,
    model_id,
    sequence_number,
    parameter_value,
    description
)
SELECT
    e.experiment_id,
    m.model_id,
    1,
    0.15,
    'Energy relaxation model'
FROM noise_experiments e
CROSS JOIN noise_models m
WHERE e.experiment_code = 'QN-EXP-001'
AND m.model_name = 'Amplitude Damping';

INSERT INTO experiment_channels (
    experiment_id,
    model_id,
    sequence_number,
    parameter_value,
    description
)
SELECT
    e.experiment_id,
    m.model_id,
    2,
    0.10,
    'Environmental dephasing'
FROM noise_experiments e
CROSS JOIN noise_models m
WHERE e.experiment_code = 'QN-EXP-001'
AND m.model_name = 'Pure Dephasing';

INSERT INTO experiment_channels (
    experiment_id,
    model_id,
    sequence_number,
    parameter_value,
    description
)
SELECT
    e.experiment_id,
    m.model_id,
    3,
    0.05,
    'Depolarizing gate error'
FROM noise_experiments e
CROSS JOIN noise_models m
WHERE e.experiment_code = 'QN-EXP-001'
AND m.model_name = 'Depolarizing';

-- ------------------------------------------------------------
-- 21. READOUT CALIBRATION
-- ------------------------------------------------------------

INSERT INTO readout_calibrations (
    qubit_id,
    p_zero_to_one,
    p_one_to_zero,
    calibration_shots,
    calibrated_by
)
SELECT
    q.qubit_id,
    0.03,
    0.05,
    10000,
    'readout-engineer'
FROM quantum_qubits q
JOIN quantum_devices d
    ON d.device_id = q.device_id
WHERE d.device_name = 'QPU-ALPHA'
AND q.physical_index = 0;

-- ------------------------------------------------------------
-- 22. SAMPLE OBSERVATIONS
-- ------------------------------------------------------------

INSERT INTO noise_observations (
    experiment_id,
    observation_type,
    observed_x,
    observed_y,
    observed_z,
    measured_zero,
    measured_one,
    estimated_fidelity
)
SELECT
    experiment_id,
    'SIMULATED',
    0.70,
    0.02,
    0.10,
    5200,
    4800,
    0.91
FROM noise_experiments
WHERE experiment_code = 'QN-EXP-001';

-- ------------------------------------------------------------
-- 23. VALIDATION QUERIES
-- ------------------------------------------------------------

-- Retrieve registered noise mechanisms.
SELECT
    source_name,
    category,
    affected_property,
    physical_mechanism
FROM noise_sources
ORDER BY category;

-- Retrieve models and parameter ranges.
SELECT
    model_name,
    category,
    parameter_name,
    minimum_parameter,
    maximum_parameter
FROM noise_models
WHERE is_enabled = TRUE
ORDER BY model_id;

-- Retrieve device calibration.
SELECT *
FROM v_coherence_report
ORDER BY calibrated_at DESC;

-- ------------------------------------------------------------
-- 24. EXPERIMENT WORKFLOW
-- ------------------------------------------------------------

-- Validate experiment configuration.
UPDATE noise_experiments
SET status = 'VALIDATED'
WHERE experiment_code = 'QN-EXP-001'
AND status = 'CREATED';

-- Start the experiment.
SELECT update_experiment_status(
    (
        SELECT experiment_id
        FROM noise_experiments
        WHERE experiment_code = 'QN-EXP-001'
    ),
    'RUNNING'
);

-- Complete the experiment.
SELECT update_experiment_status(
    (
        SELECT experiment_id
        FROM noise_experiments
        WHERE experiment_code = 'QN-EXP-001'
    ),
    'COMPLETED',
    'PASS'
);

-- ------------------------------------------------------------
-- 25. ANALYTICAL REPORTS
-- ------------------------------------------------------------

-- Channel distribution by category.
SELECT
    category,
    COUNT(*) AS channel_count,
    AVG(parameter_value) AS average_parameter
FROM v_experiment_noise_channels
GROUP BY category
ORDER BY channel_count DESC;

-- Experiment-level quality metrics.
SELECT *
FROM v_experiment_quality
ORDER BY experiment_id;

-- Compare average fidelity by experiment outcome.
SELECT
    outcome,
    COUNT(*) AS experiments,
    AVG(average_fidelity) AS mean_fidelity
FROM v_experiment_quality
GROUP BY outcome;

-- Retrieve failed and warning experiments.
SELECT
    experiment_code,
    experiment_name,
    status,
    outcome
FROM noise_experiments
WHERE status = 'FAILED'
   OR outcome IN ('FAIL', 'WARNING');

-- Retrieve latest readout calibration.
SELECT DISTINCT ON (r.qubit_id)
    d.device_name,
    q.physical_index,
    r.p_zero_to_one,
    r.p_one_to_zero,
    r.calibrated_at
FROM readout_calibrations r
JOIN quantum_qubits q
    ON q.qubit_id = r.qubit_id
JOIN quantum_devices d
    ON d.device_id = q.device_id
ORDER BY r.qubit_id, r.calibrated_at DESC;

-- ------------------------------------------------------------
-- 26. ELIGIBILITY DETERMINATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION experiment_is_merge_ready(
    p_experiment_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT
        e.status = 'COMPLETED'
        AND e.outcome = 'PASS'
        AND EXISTS (
            SELECT 1
            FROM experiment_channels ec
            WHERE ec.experiment_id = e.experiment_id
        )
        AND EXISTS (
            SELECT 1
            FROM noise_observations o
            WHERE o.experiment_id = e.experiment_id
        )
    FROM noise_experiments e
    WHERE e.experiment_id = p_experiment_id;
$$;

-- Example experiment acceptance check.
SELECT
    experiment_code,
    experiment_is_merge_ready(experiment_id) AS eligible
FROM noise_experiments;

-- ------------------------------------------------------------
-- 27. TRANSACTIONAL CALIBRATION UPDATE EXAMPLE
-- ------------------------------------------------------------

-- The following transaction demonstrates atomic calibration
-- insertion and qubit metadata update.

COMMIT;

-- Additional operational example:
--
-- BEGIN;
--
-- INSERT INTO coherence_calibrations (
--     qubit_id,
--     t1_seconds,
--     t2_seconds,
--     calibration_method,
--     calibrated_by
-- )
-- SELECT qubit_id, 110e-6, 75e-6,
--        'Updated Ramsey calibration',
--        'calibration-service'
-- FROM quantum_qubits
-- WHERE physical_index = 0
-- LIMIT 1;
--
-- UPDATE quantum_qubits
-- SET t1_seconds = 110e-6,
--     t2_seconds = 75e-6,
--     last_calibrated_at = CURRENT_TIMESTAMP
-- WHERE physical_index = 0;
--
-- COMMIT;
