DROP SCHEMA IF EXISTS shor_lab CASCADE;
CREATE SCHEMA shor_lab;

SET search_path = shor_lab, public;

-- The relational model separates circuit structure, mathematical
-- experiments, phase measurements, candidate periods, and recovered factors.

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETE',
    'FAILED',
    'TRIVIAL_FACTOR'
);

CREATE TYPE gate_type AS ENUM (
    'HADAMARD',
    'CONTROLLED_PHASE',
    'SWAP',
    'CONTROLLED_MODULAR_MULTIPLICATION',
    'MEASUREMENT'
);

CREATE TABLE experiment (
    experiment_id BIGSERIAL PRIMARY KEY,
    experiment_name TEXT NOT NULL,
    base_a BIGINT NOT NULL,
    modulus_n BIGINT NOT NULL,
    counting_qubits INTEGER NOT NULL,
    status experiment_status NOT NULL DEFAULT 'CREATED',
    discovered_period BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT experiment_base_range
        CHECK (base_a > 1 AND base_a < modulus_n),
    CONSTRAINT experiment_modulus_valid
        CHECK (modulus_n > 1),
    CONSTRAINT experiment_counting_qubits_valid
        CHECK (counting_qubits BETWEEN 1 AND 62),
    CONSTRAINT experiment_completion_consistency
        CHECK (
            (status = 'COMPLETE' AND completed_at IS NOT NULL)
            OR
            (status <> 'COMPLETE')
        ),
    CONSTRAINT experiment_period_positive
        CHECK (
            discovered_period IS NULL
            OR discovered_period > 0
        )
);

CREATE TABLE qubit_register (
    register_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    register_name TEXT NOT NULL,
    qubit_count INTEGER NOT NULL,
    register_role TEXT NOT NULL,
    UNIQUE (experiment_id, register_name),
    CONSTRAINT register_qubit_count
        CHECK (qubit_count > 0),
    CONSTRAINT register_role_nonempty
        CHECK (length(trim(register_role)) > 0)
);

CREATE TABLE circuit_gate (
    gate_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL,
    gate gate_type NOT NULL,
    control_qubit INTEGER,
    target_qubit INTEGER,
    rotation_angle NUMERIC(30, 20),
    modulus_multiplier BIGINT,
    CONSTRAINT gate_sequence_positive
        CHECK (sequence_no > 0),
    CONSTRAINT gate_qubits_valid
        CHECK (
            (gate IN ('HADAMARD', 'MEASUREMENT')
             AND target_qubit IS NOT NULL
             AND control_qubit IS NULL)
            OR
            (gate IN ('CONTROLLED_PHASE', 'CONTROLLED_MODULAR_MULTIPLICATION')
             AND control_qubit IS NOT NULL
             AND target_qubit IS NOT NULL)
            OR
            (gate = 'SWAP'
             AND control_qubit IS NOT NULL
             AND target_qubit IS NOT NULL)
        ),
    CONSTRAINT gate_distinct_qubits
        CHECK (
            control_qubit IS NULL
            OR target_qubit IS NULL
            OR control_qubit <> target_qubit
        ),
    CONSTRAINT controlled_phase_angle
        CHECK (
            gate <> 'CONTROLLED_PHASE'
            OR rotation_angle IS NOT NULL
        )
);

CREATE UNIQUE INDEX circuit_gate_order_idx
    ON circuit_gate (experiment_id, sequence_no);

CREATE TABLE phase_measurement (
    measurement_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    shot_number INTEGER NOT NULL,
    measured_integer BIGINT NOT NULL,
    counting_register_size INTEGER NOT NULL,
    measured_phase NUMERIC(30, 20) NOT NULL,
    ideal_phase NUMERIC(30, 20),
    probability NUMERIC(30, 20),
    CONSTRAINT measurement_shot_positive
        CHECK (shot_number > 0),
    CONSTRAINT measurement_integer_nonnegative
        CHECK (measured_integer >= 0),
    CONSTRAINT measurement_phase_range
        CHECK (measured_phase >= 0 AND measured_phase < 1),
    CONSTRAINT measurement_probability_range
        CHECK (
            probability IS NULL
            OR (probability >= 0 AND probability <= 1)
        )
);

CREATE INDEX phase_measurement_experiment_idx
    ON phase_measurement (experiment_id, measured_integer);

CREATE TABLE period_candidate (
    candidate_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    source_measurement_id BIGINT
        REFERENCES phase_measurement(measurement_id)
        ON DELETE SET NULL,
    candidate_period BIGINT NOT NULL,
    approximation_error NUMERIC(30, 20),
    is_even BOOLEAN GENERATED ALWAYS AS
        (candidate_period % 2 = 0) STORED,
    accepted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT candidate_period_positive
        CHECK (candidate_period > 0),
    CONSTRAINT candidate_error_nonnegative
        CHECK (
            approximation_error IS NULL
            OR approximation_error >= 0
        ),
    UNIQUE (experiment_id, candidate_period)
);

CREATE TABLE factor_result (
    factor_result_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    candidate_id BIGINT
        REFERENCES period_candidate(candidate_id)
        ON DELETE SET NULL,
    factor BIGINT NOT NULL,
    derivation TEXT NOT NULL,
    is_proper_factor BOOLEAN NOT NULL,
    CONSTRAINT factor_positive
        CHECK (factor > 1),
    CONSTRAINT factor_derivation_nonempty
        CHECK (length(trim(derivation)) > 0)
);

CREATE UNIQUE INDEX factor_result_unique_idx
    ON factor_result (experiment_id, factor);

CREATE TABLE branch_state_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT
        REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    old_status experiment_status,
    new_status experiment_status NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    message TEXT NOT NULL
);

-- A state transition audit makes workflow failures observable rather than
-- relying on the caller to maintain an external history.

CREATE OR REPLACE FUNCTION audit_experiment_status()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO branch_state_audit (
            experiment_id,
            old_status,
            new_status,
            message
        )
        VALUES (
            NEW.experiment_id,
            OLD.status,
            NEW.status,
            'Experiment status transition'
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER experiment_status_audit
AFTER UPDATE OF status ON experiment
FOR EACH ROW
EXECUTE FUNCTION audit_experiment_status();

-- Reject phase measurements that exceed the counting-register range.
CREATE OR REPLACE FUNCTION validate_measurement_range()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    register_size INTEGER;
    maximum_value BIGINT;
BEGIN
    register_size := NEW.counting_register_size;

    IF register_size < 1 OR register_size > 62 THEN
        RAISE EXCEPTION
            'counting register size must be between 1 and 62';
    END IF;

    maximum_value := (1::BIGINT << register_size) - 1;

    IF NEW.measured_integer > maximum_value THEN
        RAISE EXCEPTION
            'measurement % exceeds %-qubit register range',
            NEW.measured_integer,
            register_size;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER phase_measurement_range_check
BEFORE INSERT OR UPDATE ON phase_measurement
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_range();

-- This function evaluates the classical post-processing conditions that
-- follow period estimation: r must be even, a^(r/2) must not be ±1, and
-- gcd(x±1,N) must yield proper factors.
CREATE OR REPLACE FUNCTION evaluate_period(
    p_base BIGINT,
    p_modulus BIGINT,
    p_period BIGINT
)
RETURNS TABLE (
    valid_period BOOLEAN,
    x_value BIGINT,
    factor_minus BIGINT,
    factor_plus BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    x BIGINT;
BEGIN
    IF p_period <= 0 OR p_period % 2 <> 0 THEN
        RETURN QUERY
        SELECT FALSE, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT;
        RETURN;
    END IF;

    x := power_mod(
        p_base,
        p_period / 2,
        p_modulus
    );

    IF x = 1 OR x = p_modulus - 1 THEN
        RETURN QUERY
        SELECT FALSE, x, NULL::BIGINT, NULL::BIGINT;
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        (
            gcd(x - 1, p_modulus) > 1
            AND gcd(x - 1, p_modulus) < p_modulus
        )
        OR
        (
            gcd(x + 1, p_modulus) > 1
            AND gcd(x + 1, p_modulus) < p_modulus
        ),
        x,
        gcd(x - 1, p_modulus),
        gcd(x + 1, p_modulus);
END;
$$;

-- PostgreSQL does not provide a portable built-in power_mod function for
-- integer modular exponentiation, so the workflow uses a dedicated function.
CREATE OR REPLACE FUNCTION power_mod(
    p_base BIGINT,
    p_exponent BIGINT,
    p_modulus BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    result BIGINT := 1;
    base_value BIGINT := p_base % p_modulus;
    exponent_value BIGINT := p_exponent;
BEGIN
    IF p_modulus <= 1 THEN
        RAISE EXCEPTION 'modulus must exceed one';
    END IF;

    WHILE exponent_value > 0 LOOP
        IF exponent_value % 2 = 1 THEN
            result := (result * base_value) % p_modulus;
        END IF;

        base_value := (base_value * base_value) % p_modulus;
        exponent_value := exponent_value / 2;
    END LOOP;

    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION gcd(
    p_a BIGINT,
    p_b BIGINT
)
RETURNS BIGINT
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    a_value BIGINT := abs(p_a);
    b_value BIGINT := abs(p_b);
    remainder BIGINT;
BEGIN
    WHILE b_value <> 0 LOOP
        remainder := a_value % b_value;
        a_value := b_value;
        b_value := remainder;
    END LOOP;

    RETURN a_value;
END;
$$;

-- Re-create the period evaluation function after the helper functions exist.
CREATE OR REPLACE FUNCTION evaluate_period(
    p_base BIGINT,
    p_modulus BIGINT,
    p_period BIGINT
)
RETURNS TABLE (
    valid_period BOOLEAN,
    x_value BIGINT,
    factor_minus BIGINT,
    factor_plus BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    x BIGINT;
    minus_factor BIGINT;
    plus_factor BIGINT;
BEGIN
    IF p_period <= 0 OR p_period % 2 <> 0 THEN
        RETURN QUERY
        SELECT FALSE, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT;
        RETURN;
    END IF;

    x := power_mod(
        p_base,
        p_period / 2,
        p_modulus
    );

    IF x = 1 OR x = p_modulus - 1 THEN
        RETURN QUERY
        SELECT FALSE, x, NULL::BIGINT, NULL::BIGINT;
        RETURN;
    END IF;

    minus_factor := gcd(x - 1, p_modulus);
    plus_factor := gcd(x + 1, p_modulus);

    RETURN QUERY
    SELECT
        (
            (minus_factor > 1 AND minus_factor < p_modulus)
            OR
            (plus_factor > 1 AND plus_factor < p_modulus)
        ),
        x,
        minus_factor,
        plus_factor;
END;
$$;

CREATE VIEW experiment_summary AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.base_a,
    e.modulus_n,
    e.counting_qubits,
    e.status,
    e.discovered_period,
    count(DISTINCT pm.measurement_id) AS measurements,
    count(DISTINCT pc.candidate_id) AS period_candidates,
    count(DISTINCT fr.factor_result_id) AS recovered_factors,
    min(pm.measured_phase) AS minimum_measured_phase,
    max(pm.measured_phase) AS maximum_measured_phase
FROM experiment e
LEFT JOIN phase_measurement pm
    ON pm.experiment_id = e.experiment_id
LEFT JOIN period_candidate pc
    ON pc.experiment_id = e.experiment_id
LEFT JOIN factor_result fr
    ON fr.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    e.base_a,
    e.modulus_n,
    e.counting_qubits,
    e.status,
    e.discovered_period;

CREATE VIEW merge_eligibility_report AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.base_a,
    e.modulus_n,
    e.discovered_period,
    CASE
        WHEN e.status = 'COMPLETE'
             AND e.discovered_period IS NOT NULL
             AND e.discovered_period % 2 = 0
        THEN 'PERIOD_ELIGIBLE'
        WHEN e.status = 'TRIVIAL_FACTOR'
        THEN 'TRIVIAL_FACTOR_FOUND'
        WHEN e.status = 'FAILED'
        THEN 'FAILED'
        ELSE 'NOT_ELIGIBLE'
    END AS eligibility_state
FROM experiment e;

-- Sample experiments: 15 is the standard small demonstration modulus,
-- while a second experiment records an odd-period failure condition.
INSERT INTO experiment (
    experiment_name,
    base_a,
    modulus_n,
    counting_qubits,
    status,
    discovered_period,
    completed_at
)
VALUES
(
    'Factor 15 with base 2',
    2,
    15,
    8,
    'COMPLETE',
    4,
    now()
),
(
    'Factor 21 with base 2',
    2,
    21,
    8,
    'CREATED',
    NULL,
    NULL
),
(
    'Early GCD factor for 15',
    6,
    15,
    8,
    'TRIVIAL_FACTOR',
    NULL,
    NULL
);

INSERT INTO qubit_register (
    experiment_id,
    register_name,
    qubit_count,
    register_role
)
SELECT
    experiment_id,
    'counting',
    counting_qubits,
    'Phase-estimation counting register'
FROM experiment
WHERE experiment_name = 'Factor 15 with base 2';

INSERT INTO qubit_register (
    experiment_id,
    register_name,
    qubit_count,
    register_role
)
SELECT
    experiment_id,
    'work',
    4,
    'Modular exponentiation work register'
FROM experiment
WHERE experiment_name = 'Factor 15 with base 2';

-- Representative QFT decomposition for the counting register.
INSERT INTO circuit_gate (
    experiment_id,
    sequence_no,
    gate,
    control_qubit,
    target_qubit,
    rotation_angle
)
SELECT
    e.experiment_id,
    v.sequence_no,
    v.gate::gate_type,
    v.control_qubit,
    v.target_qubit,
    v.rotation_angle
FROM experiment e
CROSS JOIN (
    VALUES
        (1, 'HADAMARD', NULL, 0, NULL::NUMERIC),
        (2, 'CONTROLLED_PHASE', 1, 0, pi() / 2),
        (3, 'CONTROLLED_PHASE', 2, 0, pi() / 4),
        (4, 'CONTROLLED_PHASE', 3, 0, pi() / 8),
        (5, 'HADAMARD', NULL, 1, NULL::NUMERIC),
        (6, 'CONTROLLED_PHASE', 2, 1, pi() / 2),
        (7, 'CONTROLLED_PHASE', 3, 1, pi() / 4),
        (8, 'HADAMARD', NULL, 2, NULL::NUMERIC),
        (9, 'CONTROLLED_PHASE', 3, 2, pi() / 2),
        (10, 'HADAMARD', NULL, 3, NULL::NUMERIC),
        (11, 'SWAP', 0, 3, NULL::NUMERIC),
        (12, 'SWAP', 1, 2, NULL::NUMERIC)
) AS v(
    sequence_no,
    gate,
    control_qubit,
    target_qubit,
    rotation_angle
)
WHERE e.experiment_name = 'Factor 15 with base 2';

-- Idealized phase-estimation measurements for r=4:
-- phases 0, 1/4, 1/2 and 3/4 map to 0, 64, 128 and 192
-- in an eight-qubit counting register.
INSERT INTO phase_measurement (
    experiment_id,
    shot_number,
    measured_integer,
    counting_register_size,
    measured_phase,
    ideal_phase,
    probability
)
SELECT
    e.experiment_id,
    v.shot_number,
    v.measured_integer,
    8,
    v.measured_integer / 256.0,
    v.ideal_phase,
    v.probability
FROM experiment e
CROSS JOIN (
    VALUES
        (1, 0, 0.00000000000000000000::NUMERIC, 0.25::NUMERIC),
        (2, 64, 0.25000000000000000000::NUMERIC, 0.25::NUMERIC),
        (3, 128, 0.50000000000000000000::NUMERIC, 0.25::NUMERIC),
        (4, 192, 0.75000000000000000000::NUMERIC, 0.25::NUMERIC)
) AS v(
    shot_number,
    measured_integer,
    ideal_phase,
    probability
)
WHERE e.experiment_name = 'Factor 15 with base 2';

INSERT INTO period_candidate (
    experiment_id,
    source_measurement_id,
    candidate_period,
    approximation_error,
    accepted
)
SELECT
    e.experiment_id,
    pm.measurement_id,
    4,
    abs(pm.measured_phase - 0.25),
    TRUE
FROM experiment e
JOIN phase_measurement pm
    ON pm.experiment_id = e.experiment_id
WHERE e.experiment_name = 'Factor 15 with base 2'
  AND pm.measured_integer = 64;

INSERT INTO factor_result (
    experiment_id,
    candidate_id,
    factor,
    derivation,
    is_proper_factor
)
SELECT
    pc.experiment_id,
    pc.candidate_id,
    v.factor,
    v.derivation,
    TRUE
FROM period_candidate pc
CROSS JOIN (
    VALUES
        (
            3::BIGINT,
            'gcd(2^(4/2)-1, 15) = gcd(3, 15)'
        ),
        (
            5::BIGINT,
            'gcd(2^(4/2)+1, 15) = gcd(5, 15)'
        )
) AS v(factor, derivation)
WHERE pc.candidate_period = 4;

-- Transactional status update: the experiment cannot be marked complete
-- unless its period is represented by the database state.
BEGIN;

UPDATE experiment
SET
    status = 'COMPLETE',
    discovered_period = 4,
    completed_at = now()
WHERE experiment_name = 'Factor 15 with base 2'
  AND EXISTS (
      SELECT 1
      FROM period_candidate pc
      WHERE pc.experiment_id = experiment.experiment_id
        AND pc.candidate_period = 4
        AND pc.accepted
  );

COMMIT;

-- Retrieval: experiment and component structure.
SELECT *
FROM experiment_summary
ORDER BY experiment_id;

-- QFT gate inventory.
SELECT
    gate,
    count(*) AS gate_count
FROM circuit_gate
GROUP BY gate
ORDER BY gate;

-- Phase-estimation observations and rational reconstruction input.
SELECT
    e.experiment_name,
    pm.shot_number,
    pm.measured_integer,
    pm.measured_phase,
    pc.candidate_period,
    pc.accepted
FROM experiment e
JOIN phase_measurement pm
    ON pm.experiment_id = e.experiment_id
LEFT JOIN period_candidate pc
    ON pc.source_measurement_id = pm.measurement_id
ORDER BY e.experiment_id, pm.shot_number;

-- Factor-recovery report.
SELECT
    e.experiment_name,
    e.base_a,
    e.modulus_n,
    e.discovered_period,
    fr.factor,
    fr.derivation
FROM experiment e
JOIN factor_result fr
    ON fr.experiment_id = e.experiment_id
ORDER BY e.experiment_id, fr.factor;

-- Explicit evaluation of the candidate period.
SELECT *
FROM evaluate_period(2, 15, 4);

-- Failure case: odd candidate period cannot produce Shor's
-- x = a^(r/2) factor extraction step.
SELECT *
FROM evaluate_period(2, 15, 3);

-- Early classical GCD detection avoids quantum period estimation when
-- the chosen base shares a factor with N.
SELECT
    gcd(6, 15) AS early_factor;

-- Aggregation by experiment status.
SELECT
    status,
    count(*) AS experiment_count
FROM experiment
GROUP BY status
ORDER BY status;

-- Audit trail showing state transitions.
SELECT
    experiment_id,
    old_status,
    new_status,
    event_time,
    message
FROM branch_state_audit
ORDER BY event_time, audit_id;
