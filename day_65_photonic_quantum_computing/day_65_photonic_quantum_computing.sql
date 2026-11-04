-- ============================================================
-- PHOTONIC QUANTUM COMPUTING: PHOTONS AS QUBITS
-- PostgreSQL 15+
--
-- Relational experiment-management system for:
-- 1. Photonic sources
-- 2. Polarization qubits
-- 3. Optical components
-- 4. Circuit configurations
-- 5. Optical channels
-- 6. Photon transmission and detection
-- 7. Experimental runs
-- 8. Measurement results
-- 9. Loss accounting
-- 10. Hong-Ou-Mandel interference
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS photonics;

SET search_path TO photonics, public;

-- ------------------------------------------------------------
-- 1. DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE polarization_basis AS ENUM (
    'HORIZONTAL_VERTICAL',
    'DIAGONAL_ANTIDIAGONAL',
    'CIRCULAR'
);

CREATE TYPE component_type AS ENUM (
    'PHOTON_SOURCE',
    'BEAM_SPLITTER',
    'PHASE_SHIFTER',
    'POLARIZER',
    'WAVE_PLATE',
    'DETECTOR',
    'OPTICAL_CHANNEL'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE photon_status AS ENUM (
    'GENERATED',
    'TRANSMITTED',
    'LOST',
    'DETECTED'
);

CREATE TYPE measurement_outcome AS ENUM (
    'H',
    'V'
);

CREATE TYPE experiment_kind AS ENUM (
    'POLARIZATION',
    'BEAM_SPLITTER',
    'HONG_OU_MANDEL',
    'PHOTON_LOSS'
);

-- ------------------------------------------------------------
-- 2. PHOTON SOURCES
-- ------------------------------------------------------------

CREATE TABLE photon_sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_name VARCHAR(150) NOT NULL UNIQUE,

    source_type VARCHAR(60) NOT NULL,

    wavelength_nm NUMERIC(10,3) NOT NULL,

    spectral_bandwidth_nm NUMERIC(10,3) NOT NULL DEFAULT 0,

    polarization polarization_basis NOT NULL,

    coherence_length_m NUMERIC(12,6),

    repetition_rate_hz NUMERIC(16,3) NOT NULL,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_wavelength
        CHECK (wavelength_nm > 0),

    CONSTRAINT valid_bandwidth
        CHECK (spectral_bandwidth_nm >= 0),

    CONSTRAINT positive_repetition_rate
        CHECK (repetition_rate_hz > 0),

    CONSTRAINT valid_coherence_length
        CHECK (
            coherence_length_m IS NULL
            OR coherence_length_m > 0
        )
);

-- ------------------------------------------------------------
-- 3. OPTICAL COMPONENTS
-- ------------------------------------------------------------

CREATE TABLE optical_components (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    component_name VARCHAR(150) NOT NULL UNIQUE,

    component_kind component_type NOT NULL,

    reflectivity NUMERIC(8,7),

    transmission NUMERIC(8,7),

    phase_radians NUMERIC(14,10),

    insertion_loss_db NUMERIC(10,5),

    calibrated BOOLEAN NOT NULL DEFAULT FALSE,

    calibration_date DATE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_reflectivity
        CHECK (
            reflectivity IS NULL
            OR reflectivity BETWEEN 0 AND 1
        ),

    CONSTRAINT valid_transmission
        CHECK (
            transmission IS NULL
            OR transmission BETWEEN 0 AND 1
        ),

    CONSTRAINT valid_insertion_loss
        CHECK (
            insertion_loss_db IS NULL
            OR insertion_loss_db >= 0
        ),

    CONSTRAINT calibration_consistency
        CHECK (
            calibrated = FALSE
            OR calibration_date IS NOT NULL
        )
);

-- ------------------------------------------------------------
-- 4. EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_name VARCHAR(200) NOT NULL,

    experiment_type experiment_kind NOT NULL,

    source_id BIGINT NOT NULL
        REFERENCES photon_sources(source_id),

    basis polarization_basis NOT NULL,

    initial_alpha_real DOUBLE PRECISION NOT NULL,

    initial_alpha_imag DOUBLE PRECISION NOT NULL DEFAULT 0,

    initial_beta_real DOUBLE PRECISION NOT NULL,

    initial_beta_imag DOUBLE PRECISION NOT NULL DEFAULT 0,

    expected_shots INTEGER NOT NULL,

    random_seed BIGINT NOT NULL DEFAULT 42,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CONSTRAINT positive_shots
        CHECK (expected_shots > 0),

    CONSTRAINT finite_amplitudes
        CHECK (
            initial_alpha_real NOT IN (
                'Infinity'::FLOAT8,
                '-Infinity'::FLOAT8,
                'NaN'::FLOAT8
            )
            AND initial_alpha_imag NOT IN (
                'Infinity'::FLOAT8,
                '-Infinity'::FLOAT8,
                'NaN'::FLOAT8
            )
            AND initial_beta_real NOT IN (
                'Infinity'::FLOAT8,
                '-Infinity'::FLOAT8,
                'NaN'::FLOAT8
            )
            AND initial_beta_imag NOT IN (
                'Infinity'::FLOAT8,
                '-Infinity'::FLOAT8,
                'NaN'::FLOAT8
            )
        ),

    CONSTRAINT normalized_initial_state
        CHECK (
            ABS(
                initial_alpha_real * initial_alpha_real
                + initial_alpha_imag * initial_alpha_imag
                + initial_beta_real * initial_beta_real
                + initial_beta_imag * initial_beta_imag
                - 1.0
            ) < 0.00000001
        ),

    CONSTRAINT valid_experiment_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NOT NULL
        )
);

-- ------------------------------------------------------------
-- 5. CIRCUIT COMPONENT SEQUENCE
-- ------------------------------------------------------------

CREATE TABLE experiment_components (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    sequence_number INTEGER NOT NULL,

    component_id BIGINT NOT NULL
        REFERENCES optical_components(component_id),

    PRIMARY KEY (
        experiment_id,
        sequence_number
    ),

    CONSTRAINT positive_sequence
        CHECK (sequence_number > 0)
);

-- ------------------------------------------------------------
-- 6. OPTICAL CHANNEL CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE optical_channels (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    channel_name VARCHAR(150) NOT NULL UNIQUE,

    transmission_probability NUMERIC(8,7) NOT NULL,

    detector_efficiency NUMERIC(8,7) NOT NULL,

    dark_count_rate_hz NUMERIC(16,5) NOT NULL DEFAULT 0,

    mean_photon_number NUMERIC(12,8),

    CONSTRAINT valid_channel_transmission
        CHECK (
            transmission_probability BETWEEN 0 AND 1
        ),

    CONSTRAINT valid_detector_efficiency
        CHECK (
            detector_efficiency BETWEEN 0 AND 1
        ),

    CONSTRAINT valid_dark_count_rate
        CHECK (dark_count_rate_hz >= 0),

    CONSTRAINT valid_mean_photon_number
        CHECK (
            mean_photon_number IS NULL
            OR mean_photon_number >= 0
        )
);

CREATE TABLE experiment_channels (
    experiment_id BIGINT PRIMARY KEY
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    channel_id BIGINT NOT NULL
        REFERENCES optical_channels(channel_id)
);

-- ------------------------------------------------------------
-- 7. EXPERIMENTAL RUNS
-- ------------------------------------------------------------

CREATE TABLE experimental_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    run_number INTEGER NOT NULL,

    shots INTEGER NOT NULL,

    detected_photons INTEGER NOT NULL DEFAULT 0,

    lost_photons INTEGER NOT NULL DEFAULT 0,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, run_number),

    CONSTRAINT positive_run_number
        CHECK (run_number > 0),

    CONSTRAINT positive_run_shots
        CHECK (shots > 0),

    CONSTRAINT valid_photon_accounting
        CHECK (
            detected_photons >= 0
            AND lost_photons >= 0
            AND detected_photons + lost_photons <= shots
        )
);

-- ------------------------------------------------------------
-- 8. INDIVIDUAL PHOTON RECORDS
-- ------------------------------------------------------------

CREATE TABLE photon_events (
    photon_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES experimental_runs(run_id)
        ON DELETE CASCADE,

    photon_sequence INTEGER NOT NULL,

    status photon_status NOT NULL DEFAULT 'GENERATED',

    arrival_time_ns NUMERIC(16,7),

    detector_id BIGINT
        REFERENCES optical_components(component_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (run_id, photon_sequence),

    CONSTRAINT positive_photon_sequence
        CHECK (photon_sequence > 0),

    CONSTRAINT valid_arrival_time
        CHECK (
            arrival_time_ns IS NULL
            OR arrival_time_ns >= 0
        ),

    CONSTRAINT detected_photon_has_detector
        CHECK (
            status <> 'DETECTED'
            OR detector_id IS NOT NULL
        )
);

-- ------------------------------------------------------------
-- 9. POLARIZATION MEASUREMENTS
-- ------------------------------------------------------------

CREATE TABLE polarization_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    photon_id BIGINT NOT NULL UNIQUE
        REFERENCES photon_events(photon_id)
        ON DELETE CASCADE,

    outcome measurement_outcome NOT NULL,

    measurement_basis polarization_basis NOT NULL,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_measurement_time
        CHECK (measured_at <= CURRENT_TIMESTAMP)
);

-- ------------------------------------------------------------
-- 10. HONG-OU-MANDEL EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE interference_measurements (
    interference_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES experimental_runs(run_id)
        ON DELETE CASCADE,

    photon_overlap NUMERIC(8,7) NOT NULL,

    reflectivity NUMERIC(8,7) NOT NULL,

    coincidence_count INTEGER NOT NULL DEFAULT 0,

    bunching_count INTEGER NOT NULL DEFAULT 0,

    expected_shots INTEGER NOT NULL,

    CONSTRAINT valid_photon_overlap
        CHECK (photon_overlap BETWEEN 0 AND 1),

    CONSTRAINT valid_interference_reflectivity
        CHECK (reflectivity BETWEEN 0 AND 1),

    CONSTRAINT valid_interference_counts
        CHECK (
            coincidence_count >= 0
            AND bunching_count >= 0
            AND expected_shots > 0
            AND coincidence_count + bunching_count
                = expected_shots
        )
);

-- ------------------------------------------------------------
-- 11. AUDIT EVENTS
-- ------------------------------------------------------------

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT
        REFERENCES experiments(experiment_id),

    event_type VARCHAR(80) NOT NULL,

    event_details JSONB NOT NULL DEFAULT '{}'::JSONB,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 12. PERFORMANCE INDEXES
-- ------------------------------------------------------------

CREATE INDEX idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_source
    ON experiments(source_id);

CREATE INDEX idx_runs_experiment_status
    ON experimental_runs(experiment_id, status);

CREATE INDEX idx_photon_events_run_status
    ON photon_events(run_id, status);

CREATE INDEX idx_measurements_outcome
    ON polarization_measurements(outcome, measurement_basis);

CREATE INDEX idx_audit_experiment_time
    ON experiment_audit(experiment_id, recorded_at DESC);

CREATE INDEX idx_component_calibration
    ON optical_components(calibration_date)
    WHERE calibrated = TRUE;

-- ------------------------------------------------------------
-- 13. NORMALIZATION VALIDATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_quantum_state(
    p_alpha_real DOUBLE PRECISION,
    p_alpha_imag DOUBLE PRECISION,
    p_beta_real DOUBLE PRECISION,
    p_beta_imag DOUBLE PRECISION
)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT
        ABS(
            p_alpha_real * p_alpha_real
            + p_alpha_imag * p_alpha_imag
            + p_beta_real * p_beta_real
            + p_beta_imag * p_beta_imag
            - 1.0
        ) < 0.00000001
        AND p_alpha_real NOT IN (
            'Infinity'::FLOAT8,
            '-Infinity'::FLOAT8,
            'NaN'::FLOAT8
        )
        AND p_alpha_imag NOT IN (
            'Infinity'::FLOAT8,
            '-Infinity'::FLOAT8,
            'NaN'::FLOAT8
        )
        AND p_beta_real NOT IN (
            'Infinity'::FLOAT8,
            '-Infinity'::FLOAT8,
            'NaN'::FLOAT8
        )
        AND p_beta_imag NOT IN (
            'Infinity'::FLOAT8,
            '-Infinity'::FLOAT8,
            'NaN'::FLOAT8
        );
$$;

-- ------------------------------------------------------------
-- 14. HONG-OU-MANDEL PREDICTION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION predict_coincidence_probability(
    p_overlap NUMERIC,
    p_reflectivity NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF p_overlap < 0 OR p_overlap > 1 THEN
        RAISE EXCEPTION 'Overlap must be between 0 and 1';
    END IF;

    IF p_reflectivity < 0 OR p_reflectivity > 1 THEN
        RAISE EXCEPTION 'Reflectivity must be between 0 and 1';
    END IF;

    RETURN (
        4 * p_reflectivity
        * (1 - p_reflectivity)
        * (1 - p_overlap)
    );
END;
$$;

-- ------------------------------------------------------------
-- 15. EXPERIMENT STATE TRANSITION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
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
       AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status
ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ------------------------------------------------------------
-- 16. PHOTON STATUS TRANSITION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_photon_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'GENERATED'
            AND NEW.status IN ('TRANSMITTED', 'LOST'))
        OR
        (OLD.status = 'TRANSMITTED'
            AND NEW.status IN ('DETECTED', 'LOST'))
    ) THEN
        RAISE EXCEPTION
            'Invalid photon transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_photon_transition
BEFORE UPDATE OF status
ON photon_events
FOR EACH ROW
EXECUTE FUNCTION enforce_photon_transition();

-- ------------------------------------------------------------
-- 17. MEASUREMENT INTEGRITY
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_measurement_photon()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_status photon_status;
BEGIN
    SELECT status
    INTO v_status
    FROM photon_events
    WHERE photon_id = NEW.photon_id;

    IF v_status IS DISTINCT FROM 'DETECTED' THEN
        RAISE EXCEPTION
            'Only detected photons can be measured';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_measurement_photon
BEFORE INSERT OR UPDATE
ON polarization_measurements
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_photon();

-- ------------------------------------------------------------
-- 18. AUTOMATIC EXPERIMENT AUDIT
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_experiment_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
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

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_audit
AFTER UPDATE OF status
ON experiments
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION audit_experiment_changes();

-- ------------------------------------------------------------
-- 19. EXPERIMENTAL ELIGIBILITY VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_eligibility AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    s.source_name,
    s.wavelength_nm,
    s.enabled AS source_enabled,

    EXISTS (
        SELECT 1
        FROM experiment_components ec
        JOIN optical_components oc
            ON oc.component_id = ec.component_id
        WHERE ec.experiment_id = e.experiment_id
          AND oc.calibrated = FALSE
    ) AS has_uncalibrated_components,

    CASE
        WHEN s.enabled = FALSE
            THEN FALSE

        WHEN EXISTS (
            SELECT 1
            FROM experiment_components ec
            JOIN optical_components oc
                ON oc.component_id = ec.component_id
            WHERE ec.experiment_id = e.experiment_id
              AND oc.calibrated = FALSE
        )
            THEN FALSE

        ELSE TRUE
    END AS eligible_for_validation

FROM experiments e
JOIN photon_sources s
    ON s.source_id = e.source_id;

-- ------------------------------------------------------------
-- 20. MEASUREMENT AGGREGATION VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW polarization_statistics AS
SELECT
    r.run_id,
    r.experiment_id,
    COUNT(pm.measurement_id) AS measurement_count,

    COUNT(*) FILTER (
        WHERE pm.outcome = 'H'
    ) AS horizontal_count,

    COUNT(*) FILTER (
        WHERE pm.outcome = 'V'
    ) AS vertical_count,

    CASE
        WHEN COUNT(pm.measurement_id) = 0 THEN 0
        ELSE
            COUNT(*) FILTER (
                WHERE pm.outcome = 'H'
            )::NUMERIC
            / COUNT(pm.measurement_id)
    END AS horizontal_fraction

FROM experimental_runs r
LEFT JOIN photon_events pe
    ON pe.run_id = r.run_id
LEFT JOIN polarization_measurements pm
    ON pm.photon_id = pe.photon_id

GROUP BY r.run_id, r.experiment_id;

-- ------------------------------------------------------------
-- 21. RUN REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_run_report AS
SELECT
    r.run_id,
    r.experiment_id,
    r.shots,
    r.detected_photons,
    r.lost_photons,

    ROUND(
        r.detected_photons::NUMERIC
        / r.shots,
        5
    ) AS detection_rate,

    ROUND(
        r.lost_photons::NUMERIC
        / r.shots,
        5
    ) AS loss_rate,

    r.status

FROM experimental_runs r;

-- ------------------------------------------------------------
-- 22. EXPERIMENT VALIDATION PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE validate_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_eligible BOOLEAN;
    v_status experiment_status;
BEGIN
    SELECT status
    INTO v_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found: %',
            p_experiment_id;
    END IF;

    IF v_status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Only CREATED experiments can be validated';
    END IF;

    SELECT eligible_for_validation
    INTO v_eligible
    FROM experiment_eligibility
    WHERE experiment_id = p_experiment_id;

    IF NOT v_eligible THEN
        RAISE EXCEPTION
            'Experiment is not eligible for validation';
    END IF;

    UPDATE experiments
    SET status = 'VALIDATED'
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ------------------------------------------------------------
-- 23. SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO photon_sources (
    source_name,
    source_type,
    wavelength_nm,
    spectral_bandwidth_nm,
    polarization,
    coherence_length_m,
    repetition_rate_hz
)
VALUES
(
    'Laser Polarization Source A',
    'LASER',
    810.000,
    0.500,
    'HORIZONTAL_VERTICAL',
    0.002,
    80000000
),
(
    'Heralded Single Photon Source B',
    'SPDC',
    810.000,
    1.200,
    'DIAGONAL_ANTIDIAGONAL',
    0.001,
    1000000
);

INSERT INTO optical_components (
    component_name,
    component_kind,
    reflectivity,
    transmission,
    phase_radians,
    insertion_loss_db,
    calibrated,
    calibration_date
)
VALUES
(
    'Balanced Beam Splitter',
    'BEAM_SPLITTER',
    0.5,
    0.5,
    0,
    0.15,
    TRUE,
    CURRENT_DATE
),
(
    'Phase Shifter A',
    'PHASE_SHIFTER',
    NULL,
    1.0,
    1.5707963268,
    0.05,
    TRUE,
    CURRENT_DATE
),
(
    'Uncalibrated Polarizer',
    'POLARIZER',
    NULL,
    0.9,
    NULL,
    0.20,
    FALSE,
    NULL
),
(
    'Single Photon Detector A',
    'DETECTOR',
    NULL,
    NULL,
    NULL,
    0,
    TRUE,
    CURRENT_DATE
),
(
    'Quarter Wave Plate A',
    'WAVE_PLATE',
    NULL,
    1.0,
    1.5707963268,
    0.10,
    TRUE,
    CURRENT_DATE
);

INSERT INTO optical_channels (
    channel_name,
    transmission_probability,
    detector_efficiency,
    dark_count_rate_hz,
    mean_photon_number
)
VALUES
(
    'Laboratory Optical Channel',
    0.85,
    0.90,
    10,
    1.0
),
(
    'High Loss Channel',
    0.35,
    0.65,
    25,
    1.0
);

-- Experiment 1: horizontal polarization superposition.
INSERT INTO experiments (
    experiment_name,
    experiment_type,
    source_id,
    basis,
    initial_alpha_real,
    initial_alpha_imag,
    initial_beta_real,
    initial_beta_imag,
    expected_shots,
    random_seed
)
SELECT
    'Polarization Superposition Experiment',
    'POLARIZATION',
    source_id,
    'HORIZONTAL_VERTICAL',
    0.7071067811865476,
    0,
    0.7071067811865476,
    0,
    10000,
    42
FROM photon_sources
WHERE source_name = 'Laser Polarization Source A';

-- Experiment 2: Hong-Ou-Mandel experiment.
INSERT INTO experiments (
    experiment_name,
    experiment_type,
    source_id,
    basis,
    initial_alpha_real,
    initial_alpha_imag,
    initial_beta_real,
    initial_beta_imag,
    expected_shots,
    random_seed
)
SELECT
    'Hong Ou Mandel Interference Experiment',
    'HONG_OU_MANDEL',
    source_id,
    'HORIZONTAL_VERTICAL',
    1,
    0,
    0,
    0,
    5000,
    84
FROM photon_sources
WHERE source_name = 'Heralded Single Photon Source B';

-- Experiment 3: an intentionally ineligible experiment.
INSERT INTO experiments (
    experiment_name,
    experiment_type,
    source_id,
    basis,
    initial_alpha_real,
    initial_alpha_imag,
    initial_beta_real,
    initial_beta_imag,
    expected_shots,
    random_seed
)
SELECT
    'Calibration Failure Demonstration',
    'POLARIZATION',
    source_id,
    'HORIZONTAL_VERTICAL',
    1,
    0,
    0,
    0,
    1000,
    126
FROM photon_sources
WHERE source_name = 'Laser Polarization Source A';

-- Circuit components for experiment 1.
INSERT INTO experiment_components (
    experiment_id,
    sequence_number,
    component_id
)
SELECT
    e.experiment_id,
    v.sequence_number,
    oc.component_id
FROM experiments e
CROSS JOIN (
    VALUES
        (1, 'Balanced Beam Splitter'),
        (2, 'Phase Shifter A'),
        (3, 'Quarter Wave Plate A')
) AS v(sequence_number, component_name)
JOIN optical_components oc
    ON oc.component_name = v.component_name
WHERE e.experiment_name =
    'Polarization Superposition Experiment';

-- The third experiment deliberately contains an uncalibrated component.
INSERT INTO experiment_components (
    experiment_id,
    sequence_number,
    component_id
)
SELECT
    e.experiment_id,
    1,
    oc.component_id
FROM experiments e
JOIN optical_components oc
    ON oc.component_name = 'Uncalibrated Polarizer'
WHERE e.experiment_name =
    'Calibration Failure Demonstration';

-- Attach channels.
INSERT INTO experiment_channels (
    experiment_id,
    channel_id
)
SELECT
    e.experiment_id,
    c.channel_id
FROM experiments e
JOIN optical_channels c
    ON c.channel_name = 'Laboratory Optical Channel'
WHERE e.experiment_name =
    'Polarization Superposition Experiment';

INSERT INTO experiment_channels (
    experiment_id,
    channel_id
)
SELECT
    e.experiment_id,
    c.channel_id
FROM experiments e
JOIN optical_channels c
    ON c.channel_name = 'High Loss Channel'
WHERE e.experiment_name =
    'Hong Ou Mandel Interference Experiment';

-- ------------------------------------------------------------
-- 24. WORKFLOW PROCESSING
-- ------------------------------------------------------------

CALL validate_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_name =
            'Polarization Superposition Experiment'
    )
);

CALL validate_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_name =
            'Hong Ou Mandel Interference Experiment'
    )
);

-- The calibration failure experiment remains CREATED.
-- It cannot pass validation.

-- ------------------------------------------------------------
-- 25. RUN CREATION
-- ------------------------------------------------------------

INSERT INTO experimental_runs (
    experiment_id,
    run_number,
    shots,
    status
)
SELECT
    experiment_id,
    1,
    expected_shots,
    'VALIDATED'
FROM experiments
WHERE status = 'VALIDATED';

-- ------------------------------------------------------------
-- 26. PHOTON EVENT SAMPLE
-- ------------------------------------------------------------

INSERT INTO photon_events (
    run_id,
    photon_sequence,
    status
)
SELECT
    r.run_id,
    g.sequence_number,
    CASE
        WHEN g.sequence_number % 10 = 0
            THEN 'LOST'::photon_status
        WHEN g.sequence_number % 3 = 0
            THEN 'TRANSMITTED'::photon_status
        ELSE 'DETECTED'::photon_status
    END
FROM experimental_runs r
CROSS JOIN generate_series(1, 30)
    AS g(sequence_number);

-- Associate detector with detected photons.
UPDATE photon_events pe
SET detector_id = oc.component_id
FROM optical_components oc
WHERE oc.component_name = 'Single Photon Detector A'
  AND pe.status = 'DETECTED';

-- ------------------------------------------------------------
-- 27. SAMPLE POLARIZATION MEASUREMENTS
-- ------------------------------------------------------------

INSERT INTO polarization_measurements (
    photon_id,
    outcome,
    measurement_basis
)
SELECT
    pe.photon_id,

    CASE
        WHEN pe.photon_sequence % 2 = 0
            THEN 'H'::measurement_outcome
        ELSE 'V'::measurement_outcome
    END,

    'HORIZONTAL_VERTICAL'

FROM photon_events pe
WHERE pe.status = 'DETECTED';

-- ------------------------------------------------------------
-- 28. RUN ACCOUNTING
-- ------------------------------------------------------------

UPDATE experimental_runs r
SET
    detected_photons = (
        SELECT COUNT(*)
        FROM photon_events pe
        WHERE pe.run_id = r.run_id
          AND pe.status = 'DETECTED'
    ),

    lost_photons = (
        SELECT COUNT(*)
        FROM photon_events pe
        WHERE pe.run_id = r.run_id
          AND pe.status = 'LOST'
    );

-- ------------------------------------------------------------
-- 29. INTERFERENCE DATA
-- ------------------------------------------------------------

INSERT INTO interference_measurements (
    run_id,
    photon_overlap,
    reflectivity,
    coincidence_count,
    bunching_count,
    expected_shots
)
SELECT
    run_id,
    1.0,
    0.5,
    0,
    100,
    100
FROM experimental_runs
WHERE experiment_id = (
    SELECT experiment_id
    FROM experiments
    WHERE experiment_name =
        'Hong Ou Mandel Interference Experiment'
);

-- ------------------------------------------------------------
-- 30. QUERY: EXPERIMENT RETRIEVAL
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    e.experiment_name,
    e.experiment_type,
    e.status,
    s.source_name,
    e.expected_shots
FROM experiments e
JOIN photon_sources s
    ON s.source_id = e.source_id
ORDER BY e.experiment_id;

-- ------------------------------------------------------------
-- 31. QUERY: ELIGIBILITY
-- ------------------------------------------------------------

SELECT
    experiment_name,
    eligible_for_validation,
    has_uncalibrated_components
FROM experiment_eligibility
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- 32. QUERY: MEASUREMENT AGGREGATION
-- ------------------------------------------------------------

SELECT
    run_id,
    experiment_id,
    measurement_count,
    horizontal_count,
    vertical_count,
    horizontal_fraction
FROM polarization_statistics
ORDER BY run_id;

-- ------------------------------------------------------------
-- 33. QUERY: LOSS AND DETECTION REPORT
-- ------------------------------------------------------------

SELECT
    r.run_id,
    e.experiment_name,
    r.shots,
    r.detected_photons,
    r.lost_photons,
    rr.detection_rate,
    rr.loss_rate
FROM experimental_runs r
JOIN experiments e
    ON e.experiment_id = r.experiment_id
JOIN experiment_run_report rr
    ON rr.run_id = r.run_id
ORDER BY r.run_id;

-- ------------------------------------------------------------
-- 34. QUERY: THEORETICAL INTERFERENCE
-- ------------------------------------------------------------

SELECT
    overlap,
    reflectivity,
    predict_coincidence_probability(
        overlap,
        reflectivity
    ) AS expected_coincidence_probability
FROM (
    VALUES
        (0.0::NUMERIC, 0.5::NUMERIC),
        (0.5::NUMERIC, 0.5::NUMERIC),
        (1.0::NUMERIC, 0.5::NUMERIC)
) AS parameters(overlap, reflectivity);

-- ------------------------------------------------------------
-- 35. QUERY: EXPERIMENT COMPONENT ORDER
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    ec.sequence_number,
    oc.component_name,
    oc.component_kind,
    oc.calibrated
FROM experiment_components ec
JOIN experiments e
    ON e.experiment_id = ec.experiment_id
JOIN optical_components oc
    ON oc.component_id = ec.component_id
ORDER BY
    e.experiment_id,
    ec.sequence_number;

-- ------------------------------------------------------------
-- 36. QUERY: CTE-BASED PERFORMANCE REPORT
-- ------------------------------------------------------------

WITH run_totals AS (
    SELECT
        experiment_id,
        SUM(shots) AS total_shots,
        SUM(detected_photons) AS total_detected,
        SUM(lost_photons) AS total_lost
    FROM experimental_runs
    GROUP BY experiment_id
)
SELECT
    e.experiment_name,
    COALESCE(t.total_shots, 0) AS shots,
    COALESCE(t.total_detected, 0) AS detected,
    COALESCE(t.total_lost, 0) AS lost,

    CASE
        WHEN COALESCE(t.total_shots, 0) = 0 THEN 0
        ELSE ROUND(
            t.total_detected::NUMERIC
            / t.total_shots,
            4
        )
    END AS detection_rate

FROM experiments e
LEFT JOIN run_totals t
    ON t.experiment_id = e.experiment_id;

-- ------------------------------------------------------------
-- 37. QUERY: INVALID STATE VALIDATION
-- ------------------------------------------------------------

SELECT
    validate_quantum_state(
        0.7071067811865476,
        0,
        0.7071067811865476,
        0
    ) AS valid_superposition,

    validate_quantum_state(
        2,
        0,
        0,
        0
    ) AS invalid_non_normalized_state;

-- ------------------------------------------------------------
-- 38. QUERY: AUDIT HISTORY
-- ------------------------------------------------------------

SELECT
    audit_id,
    experiment_id,
    event_type,
    event_details,
    recorded_at
FROM experiment_audit
ORDER BY recorded_at DESC;

-- ------------------------------------------------------------
-- 39. TRANSACTIONAL FAILURE DEMONSTRATION
-- ------------------------------------------------------------

-- The invalid state violates the normalized-state constraint.
-- The nested transaction block rolls back only its own work.

DO $$
BEGIN
    BEGIN
        INSERT INTO experiments (
            experiment_name,
            experiment_type,
            source_id,
            basis,
            initial_alpha_real,
            initial_alpha_imag,
            initial_beta_real,
            initial_beta_imag,
            expected_shots
        )
        VALUES (
            'Invalid State Rejection Test',
            'POLARIZATION',
            (
                SELECT source_id
                FROM photon_sources
                LIMIT 1
            ),
            'HORIZONTAL_VERTICAL',
            2,
            0,
            0,
            0,
            100
        );

        RAISE EXCEPTION
            'Invalid state unexpectedly accepted';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'Invalid quantum state correctly rejected.';
    END;
END;
$$;

-- ------------------------------------------------------------
-- 40. COMPLETE TRANSACTION
-- ------------------------------------------------------------

COMMIT;
