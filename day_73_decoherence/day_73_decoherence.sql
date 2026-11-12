-- ============================================================
-- QUANTUM DECOHERENCE EXPERIMENT DATABASE
-- PostgreSQL
--
-- Models:
-- 1. Quantum devices and qubits
-- 2. Environmental conditions
-- 3. T1 and T2 experiment configurations
-- 4. Pure dephasing calculations
-- 5. Time-series measurements
-- 6. Physical consistency validation
-- 7. Experiment lifecycle
-- 8. Reporting and aggregation
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;

SET search_path TO quantum_lab, public;

-- ------------------------------------------------------------
-- ENUM TYPES
-- ------------------------------------------------------------

CREATE TYPE environment_type AS ENUM (
    'isolated',
    'thermal',
    'magnetic_noise',
    'electric_noise',
    'vibrational',
    'mixed'
);

CREATE TYPE experiment_status AS ENUM (
    'created',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE measurement_basis AS ENUM (
    'x',
    'y',
    'z'
);

-- ------------------------------------------------------------
-- DEVICE REGISTRY
-- ------------------------------------------------------------

CREATE TABLE quantum_devices (
    device_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_name VARCHAR(120) NOT NULL UNIQUE,

    architecture VARCHAR(100) NOT NULL,

    manufacturer VARCHAR(120),

    operating_temperature_kelvin NUMERIC(12, 8)
        NOT NULL CHECK (
            operating_temperature_kelvin >= 0
        ),

    operating_frequency_ghz NUMERIC(12, 6)
        CHECK (
            operating_frequency_ghz > 0
        ),

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- QUBIT REGISTRY
-- ------------------------------------------------------------

CREATE TABLE qubits (
    qubit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    device_id BIGINT NOT NULL
        REFERENCES quantum_devices(device_id),

    qubit_label VARCHAR(80) NOT NULL,

    frequency_ghz NUMERIC(12, 6)
        CHECK (frequency_ghz > 0),

    UNIQUE(device_id, qubit_label)
);

-- ------------------------------------------------------------
-- ENVIRONMENTAL CONDITIONS
-- ------------------------------------------------------------

CREATE TABLE environmental_conditions (
    environment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    environment_name VARCHAR(120) NOT NULL,

    environment_category environment_type NOT NULL,

    temperature_kelvin NUMERIC(12, 8)
        NOT NULL CHECK (temperature_kelvin >= 0),

    magnetic_noise_strength NUMERIC(14, 8)
        NOT NULL DEFAULT 0 CHECK (
            magnetic_noise_strength >= 0
        ),

    electric_noise_strength NUMERIC(14, 8)
        NOT NULL DEFAULT 0 CHECK (
            electric_noise_strength >= 0
        ),

    vibration_strength NUMERIC(14, 8)
        NOT NULL DEFAULT 0 CHECK (
            vibration_strength >= 0
        ),

    isolation_level NUMERIC(5, 4)
        CHECK (
            isolation_level BETWEEN 0 AND 1
        ),

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- EXPERIMENT CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE decoherence_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(100) NOT NULL UNIQUE,

    qubit_id BIGINT NOT NULL
        REFERENCES qubits(qubit_id),

    environment_id BIGINT NOT NULL
        REFERENCES environmental_conditions(environment_id),

    experiment_status experiment_status
        NOT NULL DEFAULT 'created',

    t1_microseconds NUMERIC(16, 8)
        CHECK (t1_microseconds > 0),

    t2_microseconds NUMERIC(16, 8)
        CHECK (t2_microseconds > 0),

    equilibrium_excited_population NUMERIC(12, 10)
        NOT NULL DEFAULT 0
        CHECK (
            equilibrium_excited_population BETWEEN 0 AND 1
        ),

    initial_bloch_x NUMERIC(12, 10)
        NOT NULL DEFAULT 1,

    initial_bloch_y NUMERIC(12, 10)
        NOT NULL DEFAULT 0,

    initial_bloch_z NUMERIC(12, 10)
        NOT NULL DEFAULT 0,

    simulation_duration_microseconds NUMERIC(16, 8)
        CHECK (
            simulation_duration_microseconds >= 0
        ),

    measurement_steps INTEGER
        CHECK (
            measurement_steps BETWEEN 1 AND 10000000
        ),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_bloch_initial_state CHECK (
        initial_bloch_x * initial_bloch_x
        + initial_bloch_y * initial_bloch_y
        + initial_bloch_z * initial_bloch_z
        <= 1.00000001
    ),

    CONSTRAINT valid_experiment_times CHECK (
        t1_microseconds IS NULL
        OR t2_microseconds IS NULL
        OR t2_microseconds <= 2 * t1_microseconds
    ),

    CONSTRAINT valid_experiment_timestamps CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

-- ------------------------------------------------------------
-- REVIEWABLE EXPERIMENT EVENTS
-- ------------------------------------------------------------

CREATE TABLE experiment_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES decoherence_experiments(experiment_id),

    previous_status experiment_status,

    new_status experiment_status NOT NULL,

    event_message TEXT,

    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- TIME-SERIES MEASUREMENTS
-- ------------------------------------------------------------

CREATE TABLE decoherence_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES decoherence_experiments(experiment_id),

    elapsed_time_microseconds NUMERIC(16, 8)
        NOT NULL CHECK (
            elapsed_time_microseconds >= 0
        ),

    bloch_x NUMERIC(14, 10) NOT NULL,

    bloch_y NUMERIC(14, 10) NOT NULL,

    bloch_z NUMERIC(14, 10) NOT NULL,

    coherence NUMERIC(14, 10) NOT NULL
        CHECK (coherence BETWEEN 0 AND 1),

    purity NUMERIC(14, 10) NOT NULL
        CHECK (purity BETWEEN 0 AND 1),

    ground_probability NUMERIC(14, 10) NOT NULL
        CHECK (ground_probability BETWEEN 0 AND 1),

    excited_probability NUMERIC(14, 10) NOT NULL
        CHECK (excited_probability BETWEEN 0 AND 1),

    shot_count INTEGER
        CHECK (shot_count > 0),

    UNIQUE(experiment_id, elapsed_time_microseconds),

    CONSTRAINT valid_measurement_bloch_vector CHECK (
        bloch_x * bloch_x
        + bloch_y * bloch_y
        + bloch_z * bloch_z
        <= 1.00000001
    ),

    CONSTRAINT valid_probability_sum CHECK (
        ABS(
            ground_probability + excited_probability - 1
        ) <= 0.000001
    )
);

-- ------------------------------------------------------------
-- EXPERIMENTAL T1/T2 RESULTS
-- ------------------------------------------------------------

CREATE TABLE relaxation_analysis (
    analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES decoherence_experiments(experiment_id),

    estimated_t1 NUMERIC(16, 8)
        CHECK (estimated_t1 > 0),

    estimated_t2 NUMERIC(16, 8)
        CHECK (estimated_t2 > 0),

    estimated_t_phi NUMERIC(18, 8)
        CHECK (
            estimated_t_phi > 0
            OR estimated_t_phi IS NULL
        ),

    fit_quality NUMERIC(8, 6)
        CHECK (fit_quality BETWEEN 0 AND 1),

    analysis_notes TEXT,

    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT analysis_physical_consistency CHECK (
        estimated_t1 IS NULL
        OR estimated_t2 IS NULL
        OR estimated_t2 <= 2 * estimated_t1
    )
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_experiments_qubit
    ON decoherence_experiments(qubit_id);

CREATE INDEX idx_experiments_environment
    ON decoherence_experiments(environment_id);

CREATE INDEX idx_experiments_status
    ON decoherence_experiments(experiment_status);

CREATE INDEX idx_measurements_experiment_time
    ON decoherence_measurements(
        experiment_id,
        elapsed_time_microseconds
    );

CREATE INDEX idx_experiment_events_time
    ON experiment_events(event_timestamp DESC);

CREATE INDEX idx_environment_category
    ON environmental_conditions(environment_category);

-- ------------------------------------------------------------
-- PURE DEPHASING FUNCTION
--
-- 1/T2 = 1/(2*T1) + 1/T_phi
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_t_phi(
    p_t1 NUMERIC,
    p_t2 NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    inverse_t_phi NUMERIC;
BEGIN
    IF p_t1 <= 0 OR p_t2 <= 0 THEN
        RAISE EXCEPTION 'T1 and T2 must be positive';
    END IF;

    IF p_t2 > 2 * p_t1 THEN
        RAISE EXCEPTION 'T2 cannot exceed 2*T1';
    END IF;

    inverse_t_phi :=
        1 / p_t2 - 1 / (2 * p_t1);

    IF inverse_t_phi <= 0.000000000001 THEN
        RETURN NULL;
    END IF;

    RETURN 1 / inverse_t_phi;
END;
$$;

-- ------------------------------------------------------------
-- BLOCH VECTOR PURITY FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_purity(
    p_x NUMERIC,
    p_y NUMERIC,
    p_z NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF (
        p_x * p_x +
        p_y * p_y +
        p_z * p_z
    ) > 1.00000001 THEN
        RAISE EXCEPTION 'Invalid Bloch vector';
    END IF;

    RETURN (
        1 + p_x * p_x + p_y * p_y + p_z * p_z
    ) / 2;
END;
$$;

-- ------------------------------------------------------------
-- EVENT AUDIT TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO experiment_events (
            experiment_id,
            previous_status,
            new_status,
            event_message
        )
        VALUES (
            NEW.experiment_id,
            NULL,
            NEW.experiment_status,
            'Experiment created'
        );

    ELSIF OLD.experiment_status IS DISTINCT FROM
          NEW.experiment_status THEN

        INSERT INTO experiment_events (
            experiment_id,
            previous_status,
            new_status,
            event_message
        )
        VALUES (
            NEW.experiment_id,
            OLD.experiment_status,
            NEW.experiment_status,
            'Experiment status changed'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_status
AFTER INSERT OR UPDATE OF experiment_status
ON decoherence_experiments
FOR EACH ROW
EXECUTE FUNCTION record_experiment_status();

-- ------------------------------------------------------------
-- EXPERIMENT LIFECYCLE PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE transition_experiment(
    p_experiment_id BIGINT,
    p_new_status experiment_status
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT experiment_status
    INTO current_status
    FROM decoherence_experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found';
    END IF;

    IF current_status IN ('completed', 'failed', 'cancelled') THEN
        RAISE EXCEPTION 'Terminal experiment cannot be changed';
    END IF;

    IF current_status = 'created'
       AND p_new_status NOT IN ('running', 'cancelled') THEN
        RAISE EXCEPTION 'Invalid transition from created';
    END IF;

    IF current_status = 'running'
       AND p_new_status NOT IN ('completed', 'failed', 'cancelled') THEN
        RAISE EXCEPTION 'Invalid transition from running';
    END IF;

    UPDATE decoherence_experiments
    SET
        experiment_status = p_new_status,
        started_at = CASE
            WHEN p_new_status = 'running'
            THEN COALESCE(started_at, NOW())
            ELSE started_at
        END,
        completed_at = CASE
            WHEN p_new_status IN ('completed', 'failed', 'cancelled')
            THEN NOW()
            ELSE completed_at
        END
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- MEASUREMENT INSERTION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION insert_measurement(
    p_experiment_id BIGINT,
    p_elapsed NUMERIC,
    p_x NUMERIC,
    p_y NUMERIC,
    p_z NUMERIC,
    p_shots INTEGER DEFAULT NULL
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    measurement_key BIGINT;
    computed_coherence NUMERIC;
    computed_purity NUMERIC;
BEGIN
    IF p_elapsed < 0 THEN
        RAISE EXCEPTION 'Elapsed time cannot be negative';
    END IF;

    IF p_shots IS NOT NULL AND p_shots <= 0 THEN
        RAISE EXCEPTION 'Shot count must be positive';
    END IF;

    computed_coherence :=
        SQRT(p_x * p_x + p_y * p_y);

    computed_purity :=
        calculate_purity(p_x, p_y, p_z);

    INSERT INTO decoherence_measurements (
        experiment_id,
        elapsed_time_microseconds,
        bloch_x,
        bloch_y,
        bloch_z,
        coherence,
        purity,
        ground_probability,
        excited_probability,
        shot_count
    )
    VALUES (
        p_experiment_id,
        p_elapsed,
        p_x,
        p_y,
        p_z,
        computed_coherence,
        computed_purity,
        (1 + p_z) / 2,
        (1 - p_z) / 2,
        p_shots
    )
    RETURNING measurement_id INTO measurement_key;

    RETURN measurement_key;
END;
$$;

-- ------------------------------------------------------------
-- EXPERIMENT REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_summary AS
SELECT
    e.experiment_id,
    e.experiment_code,
    e.experiment_status,
    q.qubit_label,
    d.device_name,
    env.environment_category,
    env.temperature_kelvin,
    e.t1_microseconds,
    e.t2_microseconds,
    calculate_t_phi(
        e.t1_microseconds,
        e.t2_microseconds
    ) AS theoretical_t_phi,
    COUNT(m.measurement_id) AS measurement_count,
    MIN(m.coherence) AS minimum_coherence,
    MAX(m.coherence) AS maximum_coherence,
    AVG(m.purity) AS average_purity

FROM decoherence_experiments e

JOIN qubits q
    ON q.qubit_id = e.qubit_id

JOIN quantum_devices d
    ON d.device_id = q.device_id

JOIN environmental_conditions env
    ON env.environment_id = e.environment_id

LEFT JOIN decoherence_measurements m
    ON m.experiment_id = e.experiment_id

GROUP BY
    e.experiment_id,
    q.qubit_label,
    d.device_name,
    env.environment_category,
    env.temperature_kelvin;

-- ------------------------------------------------------------
-- SAMPLE DEVICES
-- ------------------------------------------------------------

INSERT INTO quantum_devices (
    device_name,
    architecture,
    manufacturer,
    operating_temperature_kelvin,
    operating_frequency_ghz
)
VALUES
(
    'Quantum-Processor-A',
    'Superconducting Transmon',
    'Quantum Systems Laboratory',
    0.020,
    5.200
),
(
    'Quantum-Processor-B',
    'Superconducting Qubit',
    'Research Device Group',
    0.030,
    4.850
);

INSERT INTO qubits (
    device_id,
    qubit_label,
    frequency_ghz
)
SELECT
    device_id,
    'Q0',
    5.200
FROM quantum_devices
WHERE device_name = 'Quantum-Processor-A';

INSERT INTO qubits (
    device_id,
    qubit_label,
    frequency_ghz
)
SELECT
    device_id,
    'Q1',
    4.850
FROM quantum_devices
WHERE device_name = 'Quantum-Processor-B';

-- ------------------------------------------------------------
-- ENVIRONMENTAL PROFILES
-- ------------------------------------------------------------

INSERT INTO environmental_conditions (
    environment_name,
    environment_category,
    temperature_kelvin,
    magnetic_noise_strength,
    electric_noise_strength,
    vibration_strength,
    isolation_level,
    description
)
VALUES
(
    'Low Noise Cryogenic',
    'isolated',
    0.020,
    0.01,
    0.01,
    0.01,
    0.99,
    'Highly isolated low-temperature environment'
),
(
    'Thermal Disturbance',
    'thermal',
    0.050,
    0.10,
    0.10,
    0.05,
    0.75,
    'Elevated thermal disturbance'
),
(
    'Magnetic Instability',
    'magnetic_noise',
    0.020,
    0.90,
    0.10,
    0.05,
    0.70,
    'Strong magnetic fluctuations'
),
(
    'Electrical Interference',
    'electric_noise',
    0.030,
    0.10,
    0.85,
    0.05,
    0.70,
    'Electrical field fluctuations'
),
(
    'Mixed Environmental Noise',
    'mixed',
    0.040,
    0.70,
    0.60,
    0.50,
    0.40,
    'Combined environmental disturbances'
);

-- ------------------------------------------------------------
-- SAMPLE EXPERIMENTS
-- ------------------------------------------------------------

INSERT INTO decoherence_experiments (
    experiment_code,
    qubit_id,
    environment_id,
    t1_microseconds,
    t2_microseconds,
    equilibrium_excited_population,
    simulation_duration_microseconds,
    measurement_steps
)
SELECT
    'EXP-ISOLATED-001',
    q.qubit_id,
    env.environment_id,
    100,
    150,
    0,
    300,
    300
FROM qubits q
CROSS JOIN environmental_conditions env
WHERE q.qubit_label = 'Q0'
  AND env.environment_name = 'Low Noise Cryogenic';

INSERT INTO decoherence_experiments (
    experiment_code,
    qubit_id,
    environment_id,
    t1_microseconds,
    t2_microseconds,
    equilibrium_excited_population,
    simulation_duration_microseconds,
    measurement_steps
)
SELECT
    'EXP-THERMAL-001',
    q.qubit_id,
    env.environment_id,
    80,
    60,
    0.02,
    200,
    200
FROM qubits q
CROSS JOIN environmental_conditions env
WHERE q.qubit_label = 'Q0'
  AND env.environment_name = 'Thermal Disturbance';

INSERT INTO decoherence_experiments (
    experiment_code,
    qubit_id,
    environment_id,
    t1_microseconds,
    t2_microseconds,
    equilibrium_excited_population,
    simulation_duration_microseconds,
    measurement_steps
)
SELECT
    'EXP-MAGNETIC-001',
    q.qubit_id,
    env.environment_id,
    100,
    25,
    0,
    200,
    200
FROM qubits q
CROSS JOIN environmental_conditions env
WHERE q.qubit_label = 'Q0'
  AND env.environment_name = 'Magnetic Instability';

INSERT INTO decoherence_experiments (
    experiment_code,
    qubit_id,
    environment_id,
    t1_microseconds,
    t2_microseconds,
    equilibrium_excited_population,
    simulation_duration_microseconds,
    measurement_steps
)
SELECT
    'EXP-MIXED-001',
    q.qubit_id,
    env.environment_id,
    100,
    60,
    0.01,
    300,
    300
FROM qubits q
CROSS JOIN environmental_conditions env
WHERE q.qubit_label = 'Q1'
  AND env.environment_name = 'Mixed Environmental Noise';

-- ------------------------------------------------------------
-- MEASUREMENT DATA
-- ------------------------------------------------------------

-- The initial state is an equal superposition:
-- X=1, Y=0, Z=0.
--
-- Time evolution:
-- X(t) = exp(-t/T2)
-- Z(t) = Z_eq + (Z(0)-Z_eq)*exp(-t/T1)

DO $$
DECLARE
    exp RECORD;
    i INTEGER;
    elapsed NUMERIC;
    x_value NUMERIC;
    y_value NUMERIC;
    z_value NUMERIC;
    eq_z NUMERIC;
BEGIN
    FOR exp IN
        SELECT *
        FROM decoherence_experiments
        WHERE experiment_code IN (
            'EXP-ISOLATED-001',
            'EXP-THERMAL-001',
            'EXP-MAGNETIC-001',
            'EXP-MIXED-001'
        )
    LOOP
        eq_z :=
            1 - 2 * exp.equilibrium_excited_population;

        FOR i IN 0..exp.measurement_steps LOOP
            elapsed :=
                exp.simulation_duration_microseconds
                * i / exp.measurement_steps;

            x_value :=
                EXP(-elapsed / exp.t2_microseconds);

            y_value := 0;

            z_value :=
                eq_z
                + (exp.initial_bloch_z - eq_z)
                * EXP(-elapsed / exp.t1_microseconds);

            PERFORM insert_measurement(
                exp.experiment_id,
                elapsed,
                x_value,
                y_value,
                z_value,
                10000
            );
        END LOOP;
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- LIFECYCLE PROCESSING
-- ------------------------------------------------------------

DO $$
DECLARE
    experiment_record RECORD;
BEGIN
    FOR experiment_record IN
        SELECT experiment_id
        FROM decoherence_experiments
    LOOP
        CALL transition_experiment(
            experiment_record.experiment_id,
            'running'
        );

        CALL transition_experiment(
            experiment_record.experiment_id,
            'completed'
        );
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- ANALYTICAL RESULTS
-- ------------------------------------------------------------

INSERT INTO relaxation_analysis (
    experiment_id,
    estimated_t1,
    estimated_t2,
    estimated_t_phi,
    fit_quality,
    analysis_notes
)
SELECT
    experiment_id,
    t1_microseconds,
    t2_microseconds,
    calculate_t_phi(
        t1_microseconds,
        t2_microseconds
    ),
    0.995,
    'Theoretical simulation parameters used as reference estimates'
FROM decoherence_experiments;

COMMIT;

-- ============================================================
-- RETRIEVAL QUERIES
-- ============================================================

-- 1. All experiment configurations.

SELECT *
FROM experiment_summary
ORDER BY experiment_code;

-- 2. Environmental conditions and corresponding coherence.

SELECT
    env.environment_name,
    env.environment_category,
    env.temperature_kelvin,
    env.magnetic_noise_strength,
    env.electric_noise_strength,
    AVG(m.coherence) AS average_coherence,
    MIN(m.coherence) AS minimum_coherence
FROM environmental_conditions env
JOIN decoherence_experiments e
    ON e.environment_id = env.environment_id
JOIN decoherence_measurements m
    ON m.experiment_id = e.experiment_id
GROUP BY
    env.environment_id,
    env.environment_name,
    env.environment_category,
    env.temperature_kelvin,
    env.magnetic_noise_strength,
    env.electric_noise_strength
ORDER BY average_coherence DESC;

-- 3. T1/T2 comparison and pure dephasing time.

SELECT
    experiment_code,
    t1_microseconds,
    t2_microseconds,
    calculate_t_phi(
        t1_microseconds,
        t2_microseconds
    ) AS t_phi
FROM decoherence_experiments;

-- 4. Retrieve a measurement timeline.

SELECT
    e.experiment_code,
    m.elapsed_time_microseconds,
    m.coherence,
    m.purity,
    m.excited_probability
FROM decoherence_measurements m
JOIN decoherence_experiments e
    ON e.experiment_id = m.experiment_id
WHERE e.experiment_code = 'EXP-MIXED-001'
ORDER BY m.elapsed_time_microseconds;

-- 5. CTE: coherence loss over time.

WITH first_measurement AS (
    SELECT DISTINCT ON (experiment_id)
        experiment_id,
        coherence AS initial_coherence
    FROM decoherence_measurements
    ORDER BY experiment_id, elapsed_time_microseconds
),
last_measurement AS (
    SELECT DISTINCT ON (experiment_id)
        experiment_id,
        coherence AS final_coherence
    FROM decoherence_measurements
    ORDER BY experiment_id, elapsed_time_microseconds DESC
)
SELECT
    e.experiment_code,
    f.initial_coherence,
    l.final_coherence,
    f.initial_coherence - l.final_coherence
        AS coherence_loss
FROM decoherence_experiments e
JOIN first_measurement f USING (experiment_id)
JOIN last_measurement l USING (experiment_id);

-- 6. Identify experiments with strong dephasing.

SELECT
    experiment_code,
    t1_microseconds,
    t2_microseconds,
    calculate_t_phi(
        t1_microseconds,
        t2_microseconds
    ) AS t_phi
FROM decoherence_experiments
WHERE t2_microseconds < t1_microseconds;

-- 7. Status audit history.

SELECT
    e.experiment_code,
    ev.previous_status,
    ev.new_status,
    ev.event_timestamp,
    ev.event_message
FROM experiment_events ev
JOIN decoherence_experiments e
    ON e.experiment_id = ev.experiment_id
ORDER BY ev.event_timestamp;

-- 8. Measurement quality report.

SELECT
    experiment_id,
    COUNT(*) AS total_measurements,
    MIN(purity) AS minimum_purity,
    MAX(purity) AS maximum_purity,
    AVG(coherence) AS average_coherence,
    MAX(elapsed_time_microseconds) AS observation_duration
FROM decoherence_measurements
GROUP BY experiment_id
ORDER BY experiment_id;

-- 9. Environmental disturbance comparison.

SELECT
    env.environment_category,
    AVG(env.temperature_kelvin) AS average_temperature,
    AVG(env.magnetic_noise_strength) AS average_magnetic_noise,
    AVG(env.electric_noise_strength) AS average_electric_noise,
    AVG(m.coherence) AS average_coherence
FROM environmental_conditions env
JOIN decoherence_experiments e
    ON e.environment_id = env.environment_id
JOIN decoherence_measurements m
    ON m.experiment_id = e.experiment_id
GROUP BY env.environment_category
ORDER BY average_coherence DESC;

-- 10. Experiments eligible for completed reporting.

SELECT *
FROM experiment_summary
WHERE experiment_status = 'completed'
  AND measurement_count > 0;

-- ============================================================
-- VALIDATION EXAMPLES
-- ============================================================

-- Valid mathematical boundary:
SELECT calculate_t_phi(100, 200);

-- Pure dephasing example:
SELECT calculate_t_phi(100, 60);

-- Invalid T1/T2 combinations are rejected:
-- SELECT calculate_t_phi(10, 30);

-- Invalid Bloch vectors are rejected:
-- SELECT calculate_purity(1, 1, 1);

-- The database constraints independently protect against
-- invalid probability values, duplicate measurements,
-- impossible Bloch vectors and physically inconsistent T1/T2.

-- ============================================================
-- END OF QUANTUM DECOHERENCE DATABASE
-- ============================================================
