DROP SCHEMA IF EXISTS trapped_ion_control CASCADE;
CREATE SCHEMA trapped_ion_control;
SET search_path = trapped_ion_control, public;

CREATE TYPE ion_status AS ENUM (
    'available',
    'calibration_required',
    'maintenance',
    'offline'
);

CREATE TYPE pulse_type AS ENUM (
    'single_qubit',
    'entangling'
);

CREATE TYPE pulse_status AS ENUM (
    'scheduled',
    'executed',
    'rejected',
    'cancelled'
);

CREATE TYPE calibration_status AS ENUM (
    'pending',
    'passed',
    'failed',
    'expired'
);

CREATE TYPE check_status AS ENUM (
    'pending',
    'passed',
    'failed'
);

CREATE TYPE review_decision AS ENUM (
    'approved',
    'rejected'
);

CREATE TABLE trap_system (
    trap_id BIGSERIAL PRIMARY KEY,
    system_name TEXT NOT NULL UNIQUE,
    radial_frequency_mhz NUMERIC(10,4) NOT NULL,
    axial_frequency_mhz NUMERIC(10,4) NOT NULL,
    laser_wavelength_nm NUMERIC(8,3) NOT NULL,
    max_laser_power_mw NUMERIC(10,3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (radial_frequency_mhz > axial_frequency_mhz),
    CHECK (laser_wavelength_nm BETWEEN 200 AND 2000),
    CHECK (max_laser_power_mw > 0)
);

CREATE TABLE ion (
    ion_id BIGSERIAL PRIMARY KEY,
    trap_id BIGINT NOT NULL REFERENCES trap_system(trap_id),
    logical_index INTEGER NOT NULL,
    mass_amu NUMERIC(10,4) NOT NULL,
    axial_frequency_mhz NUMERIC(10,4) NOT NULL,
    status ion_status NOT NULL DEFAULT 'available',
    UNIQUE (trap_id, logical_index),
    CHECK (logical_index >= 0),
    CHECK (mass_amu > 0),
    CHECK (axial_frequency_mhz > 0)
);

CREATE TABLE laser_channel (
    laser_channel_id BIGSERIAL PRIMARY KEY,
    trap_id BIGINT NOT NULL REFERENCES trap_system(trap_id),
    channel_name TEXT NOT NULL,
    max_power_mw NUMERIC(10,3) NOT NULL,
    rabi_scale NUMERIC(12,8) NOT NULL DEFAULT 1.0,
    frequency_offset_mhz NUMERIC(12,8) NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (trap_id, channel_name),
    CHECK (max_power_mw > 0),
    CHECK (rabi_scale > 0)
);

CREATE TABLE calibration (
    calibration_id BIGSERIAL PRIMARY KEY,
    laser_channel_id BIGINT NOT NULL REFERENCES laser_channel(laser_channel_id),
    measured_rabi_mhz NUMERIC(12,6) NOT NULL,
    measured_detuning_mhz NUMERIC(12,6) NOT NULL,
    tolerance_percent NUMERIC(6,3) NOT NULL DEFAULT 5.0,
    status calibration_status NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    CHECK (measured_rabi_mhz > 0),
    CHECK (tolerance_percent > 0),
    CHECK (expires_at > measured_at)
);

CREATE TABLE control_policy (
    policy_id BIGSERIAL PRIMARY KEY,
    trap_id BIGINT NOT NULL UNIQUE REFERENCES trap_system(trap_id),
    max_detuning_mhz NUMERIC(12,6) NOT NULL,
    max_pulse_duration_ns NUMERIC(14,3) NOT NULL,
    max_power_fraction NUMERIC(8,5) NOT NULL DEFAULT 1.0,
    require_current_calibration BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (trap_id),
    CHECK (max_detuning_mhz >= 0),
    CHECK (max_pulse_duration_ns > 0),
    CHECK (max_power_fraction > 0 AND max_power_fraction <= 1)
);

CREATE TABLE experiment (
    experiment_id BIGSERIAL PRIMARY KEY,
    trap_id BIGINT NOT NULL REFERENCES trap_system(trap_id),
    experiment_name TEXT NOT NULL,
    objective TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (trap_id, experiment_name)
);

CREATE TABLE pulse_sequence (
    sequence_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiment(experiment_id),
    sequence_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (experiment_id, sequence_name)
);

CREATE TABLE pulse (
    pulse_id BIGSERIAL PRIMARY KEY,
    sequence_id BIGINT NOT NULL REFERENCES pulse_sequence(sequence_id),
    pulse_name TEXT NOT NULL,
    pulse_type pulse_type NOT NULL,
    primary_ion_id BIGINT NOT NULL REFERENCES ion(ion_id),
    target_ion_id BIGINT REFERENCES ion(ion_id),
    laser_channel_id BIGINT NOT NULL REFERENCES laser_channel(laser_channel_id),
    start_ns NUMERIC(16,3) NOT NULL,
    duration_ns NUMERIC(16,3) NOT NULL,
    rabi_frequency_mhz NUMERIC(12,6) NOT NULL,
    detuning_mhz NUMERIC(12,6) NOT NULL DEFAULT 0,
    phase_rad NUMERIC(16,10) NOT NULL DEFAULT 0,
    status pulse_status NOT NULL DEFAULT 'scheduled',
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sequence_id, pulse_name),
    CHECK (start_ns >= 0),
    CHECK (duration_ns > 0),
    CHECK (rabi_frequency_mhz > 0),
    CHECK (
        pulse_type = 'single_qubit'
        OR (
            pulse_type = 'entangling'
            AND target_ion_id IS NOT NULL
            AND target_ion_id <> primary_ion_id
        )
    ),
    CHECK (
        status <> 'rejected'
        OR rejection_reason IS NOT NULL
    )
);

CREATE TABLE calibration_run (
    calibration_run_id BIGSERIAL PRIMARY KEY,
    trap_id BIGINT NOT NULL REFERENCES trap_system(trap_id),
    run_name TEXT NOT NULL,
    status calibration_status NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (trap_id, run_name),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE control_check (
    control_check_id BIGSERIAL PRIMARY KEY,
    sequence_id BIGINT NOT NULL REFERENCES pulse_sequence(sequence_id),
    check_name TEXT NOT NULL,
    status check_status NOT NULL DEFAULT 'pending',
    details TEXT,
    checked_at TIMESTAMPTZ,
    UNIQUE (sequence_id, check_name)
);

CREATE TABLE measurement_run (
    measurement_run_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiment(experiment_id),
    shots INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (shots > 0 AND shots <= 10000000)
);

CREATE TABLE measurement_result (
    measurement_result_id BIGSERIAL PRIMARY KEY,
    measurement_run_id BIGINT NOT NULL
        REFERENCES measurement_run(measurement_run_id),
    bitstring TEXT NOT NULL,
    count INTEGER NOT NULL,
    UNIQUE (measurement_run_id, bitstring),
    CHECK (bitstring <> ''),
    CHECK (count >= 0)
);

CREATE TABLE operator (
    operator_id BIGSERIAL PRIMARY KEY,
    operator_name TEXT NOT NULL UNIQUE,
    role_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE pulse_approval (
    approval_id BIGSERIAL PRIMARY KEY,
    sequence_id BIGINT NOT NULL REFERENCES pulse_sequence(sequence_id),
    operator_id BIGINT NOT NULL REFERENCES operator(operator_id),
    decision review_decision NOT NULL,
    reason TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ion_trap_status
    ON ion(trap_id, status);

CREATE INDEX idx_pulse_sequence_timing
    ON pulse(sequence_id, start_ns);

CREATE INDEX idx_pulse_status
    ON pulse(status);

CREATE INDEX idx_calibration_channel_expiry
    ON calibration(laser_channel_id, expires_at);

CREATE INDEX idx_measurement_run_experiment
    ON measurement_run(experiment_id);

CREATE OR REPLACE FUNCTION validate_pulse_policy()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    policy_row control_policy%ROWTYPE;
    channel_row laser_channel%ROWTYPE;
    primary_ion_trap BIGINT;
    target_ion_trap BIGINT;
    effective_detuning NUMERIC;
    estimated_power NUMERIC;
    calibration_ok BOOLEAN;
BEGIN
    SELECT trap_id
    INTO primary_ion_trap
    FROM ion
    WHERE ion_id = NEW.primary_ion_id;

    IF primary_ion_trap IS NULL THEN
        RAISE EXCEPTION 'Primary ion does not exist';
    END IF;

    SELECT trap_id
    INTO target_ion_trap
    FROM ion
    WHERE ion_id = NEW.target_ion_id;

    IF NEW.target_ion_id IS NOT NULL
       AND target_ion_trap <> primary_ion_trap THEN
        RAISE EXCEPTION 'Entangling ions must belong to the same trap';
    END IF;

    SELECT *
    INTO policy_row
    FROM control_policy
    WHERE trap_id = primary_ion_trap;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No control policy exists for trap %',
            primary_ion_trap;
    END IF;

    SELECT *
    INTO channel_row
    FROM laser_channel
    WHERE laser_channel_id = NEW.laser_channel_id
      AND trap_id = primary_ion_trap
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Laser channel is inactive or belongs to another trap';
    END IF;

    effective_detuning :=
        NEW.detuning_mhz + channel_row.frequency_offset_mhz;

    IF abs(effective_detuning) > policy_row.max_detuning_mhz THEN
        RAISE EXCEPTION
            'Effective detuning % exceeds policy limit %',
            effective_detuning,
            policy_row.max_detuning_mhz;
    END IF;

    IF NEW.duration_ns > policy_row.max_pulse_duration_ns THEN
        RAISE EXCEPTION
            'Pulse duration % exceeds policy limit %',
            NEW.duration_ns,
            policy_row.max_pulse_duration_ns;
    END IF;

    estimated_power :=
        NEW.rabi_frequency_mhz *
        channel_row.rabi_scale *
        0.02;

    IF estimated_power >
       channel_row.max_power_mw * policy_row.max_power_fraction THEN
        RAISE EXCEPTION
            'Estimated optical power % exceeds permitted power',
            estimated_power;
    END IF;

    IF policy_row.require_current_calibration THEN
        SELECT EXISTS (
            SELECT 1
            FROM calibration c
            WHERE c.laser_channel_id = channel_row.laser_channel_id
              AND c.status = 'passed'
              AND c.expires_at > now()
        )
        INTO calibration_ok;

        IF NOT calibration_ok THEN
            RAISE EXCEPTION
                'Current passed calibration is required for laser channel %',
                channel_row.channel_name;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_pulse_policy
BEFORE INSERT OR UPDATE ON pulse
FOR EACH ROW
EXECUTE FUNCTION validate_pulse_policy();

CREATE OR REPLACE FUNCTION reject_overlapping_pulse()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    conflict_count INTEGER;
BEGIN
    SELECT count(*)
    INTO conflict_count
    FROM pulse p
    WHERE p.sequence_id = NEW.sequence_id
      AND p.pulse_id <> NEW.pulse_id
      AND p.status <> 'cancelled'
      AND NEW.start_ns < p.start_ns + p.duration_ns
      AND p.start_ns < NEW.start_ns + NEW.duration_ns
      AND (
          p.primary_ion_id = NEW.primary_ion_id
          OR p.primary_ion_id = NEW.target_ion_id
          OR p.target_ion_id = NEW.primary_ion_id
          OR p.target_ion_id = NEW.target_ion_id
      );

    IF conflict_count > 0 THEN
        RAISE EXCEPTION
            'Pulse conflicts with % existing pulse(s) on the same ion',
            conflict_count;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reject_overlapping_pulse
BEFORE INSERT OR UPDATE ON pulse
FOR EACH ROW
EXECUTE FUNCTION reject_overlapping_pulse();

CREATE OR REPLACE VIEW v_pulse_control_status AS
SELECT
    p.pulse_id,
    p.pulse_name,
    p.pulse_type,
    p.start_ns,
    p.duration_ns,
    p.status,
    t.system_name,
    lp.channel_name,
    i.logical_index AS primary_ion,
    ti.logical_index AS target_ion,
    c.status AS calibration_status,
    c.expires_at AS calibration_expires_at
FROM pulse p
JOIN ion i
    ON i.ion_id = p.primary_ion_id
JOIN trap_system t
    ON t.trap_id = i.trap_id
JOIN laser_channel lp
    ON lp.laser_channel_id = p.laser_channel_id
LEFT JOIN ion ti
    ON ti.ion_id = p.target_ion_id
LEFT JOIN LATERAL (
    SELECT c.status, c.expires_at
    FROM calibration c
    WHERE c.laser_channel_id = lp.laser_channel_id
    ORDER BY c.measured_at DESC
    LIMIT 1
) c ON TRUE;

CREATE OR REPLACE VIEW v_sequence_eligibility AS
WITH latest_calibration AS (
    SELECT DISTINCT ON (laser_channel_id)
        laser_channel_id,
        status,
        expires_at
    FROM calibration
    ORDER BY laser_channel_id, measured_at DESC
),
check_summary AS (
    SELECT
        sequence_id,
        count(*) FILTER (WHERE status = 'passed') AS passed_checks,
        count(*) FILTER (WHERE status = 'failed') AS failed_checks,
        count(*) AS total_checks
    FROM control_check
    GROUP BY sequence_id
),
approval_summary AS (
    SELECT
        sequence_id,
        count(*) FILTER (WHERE decision = 'approved') AS approvals,
        count(*) FILTER (WHERE decision = 'rejected') AS rejections
    FROM pulse_approval
    GROUP BY sequence_id
)
SELECT
    ps.sequence_id,
    ps.sequence_name,
    coalesce(cs.total_checks, 0) AS total_checks,
    coalesce(cs.passed_checks, 0) AS passed_checks,
    coalesce(cs.failed_checks, 0) AS failed_checks,
    coalesce(a.approvals, 0) AS approvals,
    coalesce(a.rejections, 0) AS rejections,
    CASE
        WHEN coalesce(cs.failed_checks, 0) > 0 THEN FALSE
        WHEN coalesce(cs.total_checks, 0) = 0 THEN FALSE
        WHEN coalesce(cs.passed_checks, 0) <> coalesce(cs.total_checks, 0)
            THEN FALSE
        WHEN coalesce(a.rejections, 0) > 0 THEN FALSE
        WHEN coalesce(a.approvals, 0) = 0 THEN FALSE
        ELSE TRUE
    END AS merge_eligible
FROM pulse_sequence ps
LEFT JOIN check_summary cs
    ON cs.sequence_id = ps.sequence_id
LEFT JOIN approval_summary a
    ON a.sequence_id = ps.sequence_id;

INSERT INTO trap_system (
    system_name,
    radial_frequency_mhz,
    axial_frequency_mhz,
    laser_wavelength_nm,
    max_laser_power_mw
)
VALUES (
    'Linear-Ion-Trap-01',
    4.5,
    1.0,
    397.0,
    20.0
);

INSERT INTO ion (
    trap_id,
    logical_index,
    mass_amu,
    axial_frequency_mhz,
    status
)
SELECT
    trap_id,
    x.logical_index,
    40.0,
    1.0,
    'available'
FROM trap_system
CROSS JOIN (
    VALUES (0), (1), (2)
) AS x(logical_index)
WHERE system_name = 'Linear-Ion-Trap-01';

INSERT INTO laser_channel (
    trap_id,
    channel_name,
    max_power_mw,
    rabi_scale,
    frequency_offset_mhz
)
SELECT
    trap_id,
    '397nm-control',
    20.0,
    0.98,
    0.01
FROM trap_system
WHERE system_name = 'Linear-Ion-Trap-01';

INSERT INTO calibration (
    laser_channel_id,
    measured_rabi_mhz,
    measured_detuning_mhz,
    tolerance_percent,
    status,
    expires_at
)
SELECT
    laser_channel_id,
    0.99,
    0.01,
    5.0,
    'passed',
    now() + interval '30 days'
FROM laser_channel
WHERE channel_name = '397nm-control';

INSERT INTO control_policy (
    trap_id,
    max_detuning_mhz,
    max_pulse_duration_ns,
    max_power_fraction,
    require_current_calibration
)
SELECT
    trap_id,
    5.0,
    2000.0,
    1.0,
    TRUE
FROM trap_system
WHERE system_name = 'Linear-Ion-Trap-01';

INSERT INTO experiment (
    trap_id,
    experiment_name,
    objective
)
SELECT
    trap_id,
    'two-ion-entanglement',
    'Calibrated single-qubit preparation followed by motional entangling control'
FROM trap_system
WHERE system_name = 'Linear-Ion-Trap-01';

INSERT INTO pulse_sequence (
    experiment_id,
    sequence_name
)
SELECT
    experiment_id,
    'bell-state-control-sequence'
FROM experiment
WHERE experiment_name = 'two-ion-entanglement';

INSERT INTO operator (
    operator_name,
    role_name
)
VALUES
    ('Dr. Rao', 'quantum-control-engineer'),
    ('Dr. Mehta', 'experimental-physicist');

INSERT INTO control_check (
    sequence_id,
    check_name,
    status,
    details,
    checked_at
)
SELECT
    sequence_id,
    v.check_name,
    v.status,
    v.details,
    now()
FROM pulse_sequence
CROSS JOIN (
    VALUES
        (
            'laser-calibration',
            'passed'::check_status,
            'Current passed calibration is available.'
        ),
        (
            'motional-mode-separation',
            'passed'::check_status,
            'Radial and axial frequencies satisfy the trap policy.'
        ),
        (
            'timing-conflict-check',
            'passed'::check_status,
            'No same-ion pulse overlap detected.'
        ),
        (
            'power-and-detuning-policy',
            'passed'::check_status,
            'Pulse parameters remain within configured limits.'
        )
) AS v(check_name, status, details)
WHERE sequence_name = 'bell-state-control-sequence';

INSERT INTO pulse (
    sequence_id,
    pulse_name,
    pulse_type,
    primary_ion_id,
    target_ion_id,
    laser_channel_id,
    start_ns,
    duration_ns,
    rabi_frequency_mhz,
    detuning_mhz,
    phase_rad
)
SELECT
    ps.sequence_id,
    'carrier-pi-over-two',
    'single_qubit',
    i0.ion_id,
    NULL,
    lc.laser_channel_id,
    0,
    250,
    1.0,
    0,
    0
FROM pulse_sequence ps
JOIN ion i0
    ON i0.logical_index = 0
JOIN laser_channel lc
    ON lc.channel_name = '397nm-control'
WHERE ps.sequence_name = 'bell-state-control-sequence';

INSERT INTO pulse (
    sequence_id,
    pulse_name,
    pulse_type,
    primary_ion_id,
    target_ion_id,
    laser_channel_id,
    start_ns,
    duration_ns,
    rabi_frequency_mhz,
    detuning_mhz,
    phase_rad
)
SELECT
    ps.sequence_id,
    'motional-entangling-pulse',
    'entangling',
    i0.ion_id,
    i1.ion_id,
    lc.laser_channel_id,
    1000,
    500,
    1.0,
    0,
    pi() / 2
FROM pulse_sequence ps
JOIN ion i0
    ON i0.logical_index = 0
JOIN ion i1
    ON i1.logical_index = 1
JOIN laser_channel lc
    ON lc.channel_name = '397nm-control'
WHERE ps.sequence_name = 'bell-state-control-sequence';

INSERT INTO pulse_approval (
    sequence_id,
    operator_id,
    decision,
    reason
)
SELECT
    ps.sequence_id,
    o.operator_id,
    'approved',
    'Calibration, timing, mode separation, and laser safety checks passed.'
FROM pulse_sequence ps
JOIN operator o
    ON o.operator_name = 'Dr. Rao'
WHERE ps.sequence_name = 'bell-state-control-sequence';

INSERT INTO pulse_approval (
    sequence_id,
    operator_id,
    decision,
    reason
)
SELECT
    ps.sequence_id,
    o.operator_id,
    'approved',
    'Independent experimental review completed.'
FROM pulse_sequence ps
JOIN operator o
    ON o.operator_name = 'Dr. Mehta'
WHERE ps.sequence_name = 'bell-state-control-sequence';

INSERT INTO measurement_run (
    experiment_id,
    shots
)
SELECT
    experiment_id,
    500
FROM experiment
WHERE experiment_name = 'two-ion-entanglement';

INSERT INTO measurement_result (
    measurement_run_id,
    bitstring,
    count
)
SELECT
    mr.measurement_run_id,
    v.bitstring,
    v.count
FROM measurement_run mr
CROSS JOIN (
    VALUES
        ('00', 248),
        ('11', 241),
        ('01', 6),
        ('10', 5)
) AS v(bitstring, count)
WHERE mr.shots = 500;

-- Retrieval: inspect all pulses with their latest calibration state.
SELECT *
FROM v_pulse_control_status
ORDER BY start_ns;

-- Validation: locate any failed control checks.
SELECT
    ps.sequence_name,
    cc.check_name,
    cc.status,
    cc.details
FROM control_check cc
JOIN pulse_sequence ps
    ON ps.sequence_id = cc.sequence_id
WHERE cc.status = 'failed';

-- Aggregation: calculate observed measurement frequencies.
SELECT
    mr.measurement_run_id,
    SUM(r.count) AS observed_shots,
    jsonb_object_agg(r.bitstring, r.count) AS counts,
    ROUND(
        100.0 * SUM(r.count)
        FILTER (WHERE r.bitstring IN ('00', '11'))
        / NULLIF(SUM(r.count), 0),
        2
    ) AS correlated_outcome_percent
FROM measurement_run mr
JOIN measurement_result r
    ON r.measurement_run_id = mr.measurement_run_id
GROUP BY mr.measurement_run_id;

-- Evaluation: identify sequences that satisfy all explicit approval
-- and control-check requirements.
SELECT *
FROM v_sequence_eligibility
ORDER BY sequence_id;

-- Workflow reporting: show pulse states and experimental context.
SELECT
    e.experiment_name,
    ps.sequence_name,
    p.pulse_name,
    p.pulse_type,
    p.status,
    p.start_ns,
    p.duration_ns
FROM experiment e
JOIN pulse_sequence ps
    ON ps.experiment_id = e.experiment_id
JOIN pulse p
    ON p.sequence_id = ps.sequence_id
ORDER BY p.start_ns;

-- CTE-based eligibility report.
WITH latest_calibration AS (
    SELECT DISTINCT ON (laser_channel_id)
        laser_channel_id,
        status,
        expires_at
    FROM calibration
    ORDER BY laser_channel_id, measured_at DESC
),
sequence_checks AS (
    SELECT
        sequence_id,
        bool_and(status = 'passed') AS all_checks_passed,
        count(*) AS check_count
    FROM control_check
    GROUP BY sequence_id
),
sequence_approvals AS (
    SELECT
        sequence_id,
        count(*) FILTER (WHERE decision = 'approved') AS approved_count,
        count(*) FILTER (WHERE decision = 'rejected') AS rejected_count
    FROM pulse_approval
    GROUP BY sequence_id
)
SELECT
    ps.sequence_name,
    sc.check_count,
    sc.all_checks_passed,
    sa.approved_count,
    sa.rejected_count,
    CASE
        WHEN sc.all_checks_passed
         AND sa.rejected_count = 0
         AND sa.approved_count >= 1
         AND EXISTS (
             SELECT 1
             FROM latest_calibration lc
             JOIN pulse p
               ON p.laser_channel_id = lc.laser_channel_id
              AND p.sequence_id = ps.sequence_id
             WHERE lc.status = 'passed'
               AND lc.expires_at > now()
         )
        THEN 'ELIGIBLE'
        ELSE 'BLOCKED'
    END AS eligibility
FROM pulse_sequence ps
JOIN sequence_checks sc
    ON sc.sequence_id = ps.sequence_id
JOIN sequence_approvals sa
    ON sa.sequence_id = ps.sequence_id;

-- Transactional example: update a sequence status only after all checks
-- and approvals remain valid.
BEGIN;

UPDATE pulse
SET status = 'executed'
WHERE sequence_id = (
    SELECT sequence_id
    FROM pulse_sequence
    WHERE sequence_name = 'bell-state-control-sequence'
)
AND status = 'scheduled'
AND EXISTS (
    SELECT 1
    FROM v_sequence_eligibility v
    WHERE v.sequence_id = pulse.sequence_id
      AND v.merge_eligible = TRUE
);

COMMIT;

-- Failure-case query: find any pulse whose recorded detuning is close to
-- or beyond the configured limit.
SELECT
    p.pulse_name,
    p.detuning_mhz,
    cp.max_detuning_mhz,
    CASE
        WHEN abs(
            p.detuning_mhz + lc.frequency_offset_mhz
        ) > cp.max_detuning_mhz
        THEN 'VIOLATION'
        ELSE 'WITHIN_POLICY'
    END AS policy_result
FROM pulse p
JOIN ion i
    ON i.ion_id = p.primary_ion_id
JOIN control_policy cp
    ON cp.trap_id = i.trap_id
JOIN laser_channel lc
    ON lc.laser_channel_id = p.laser_channel_id
ORDER BY p.pulse_id;
