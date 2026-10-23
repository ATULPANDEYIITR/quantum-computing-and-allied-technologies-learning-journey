DROP SCHEMA IF EXISTS quantum_phase_estimation CASCADE;
CREATE SCHEMA quantum_phase_estimation;

SET search_path = quantum_phase_estimation, public;

-- A QPE experiment is associated with a unitary eigenphase and a
-- counting-register configuration. PostgreSQL is used here to persist
-- experiments, circuit operations, probability outcomes, and measurements.

CREATE TABLE phase_unitaries (
    unitary_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unitary_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    eigenphase NUMERIC(20,16) NOT NULL,
    eigenstate_label TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT phase_unitary_phase_range
        CHECK (eigenphase >= 0 AND eigenphase < 1),
    CONSTRAINT phase_unitary_name_not_blank
        CHECK (btrim(unitary_name) <> ''),
    CONSTRAINT phase_unitary_eigenstate_not_blank
        CHECK (btrim(eigenstate_label) <> '')
);

CREATE TABLE qpe_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unitary_id BIGINT NOT NULL REFERENCES phase_unitaries(unitary_id),
    experiment_name TEXT NOT NULL UNIQUE,
    counting_qubits INTEGER NOT NULL,
    shots INTEGER NOT NULL DEFAULT 1000,
    state TEXT NOT NULL DEFAULT 'prepared',
    estimated_integer INTEGER,
    estimated_phase NUMERIC(20,16),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CONSTRAINT experiment_qubit_count
        CHECK (counting_qubits BETWEEN 1 AND 20),
    CONSTRAINT experiment_shots
        CHECK (shots BETWEEN 1 AND 100000000),
    CONSTRAINT experiment_state
        CHECK (
            state IN (
                'prepared',
                'encoded',
                'transformed',
                'measured',
                'rejected'
            )
        ),
    CONSTRAINT experiment_estimate_range
        CHECK (
            estimated_phase IS NULL
            OR (estimated_phase >= 0 AND estimated_phase < 1)
        ),
    CONSTRAINT experiment_integer_range
        CHECK (
            estimated_integer IS NULL
            OR (
                estimated_integer >= 0
                AND estimated_integer < (2 ^ counting_qubits)
            )
        )
);

CREATE TABLE qpe_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES qpe_experiments(experiment_id)
        ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL,
    operation_type TEXT NOT NULL,
    control_qubit INTEGER,
    power_exponent BIGINT,
    phase_argument NUMERIC(30,20),
    CONSTRAINT operation_sequence_positive
        CHECK (sequence_no >= 1),
    CONSTRAINT operation_type_valid
        CHECK (
            operation_type IN (
                'HADAMARD',
                'CONTROLLED_U_POWER',
                'INVERSE_QFT',
                'MEASUREMENT'
            )
        ),
    CONSTRAINT operation_control_valid
        CHECK (
            control_qubit IS NULL
            OR control_qubit >= 0
        ),
    CONSTRAINT operation_unique_sequence
        UNIQUE (experiment_id, sequence_no)
);

CREATE TABLE probability_outcomes (
    experiment_id BIGINT NOT NULL
        REFERENCES qpe_experiments(experiment_id)
        ON DELETE CASCADE,
    outcome_integer INTEGER NOT NULL,
    probability NUMERIC(24,20) NOT NULL,
    theoretical_phase NUMERIC(20,16) NOT NULL,
    PRIMARY KEY (experiment_id, outcome_integer),
    CONSTRAINT probability_range
        CHECK (probability >= 0 AND probability <= 1),
    CONSTRAINT outcome_nonnegative
        CHECK (outcome_integer >= 0),
    CONSTRAINT theoretical_phase_range
        CHECK (
            theoretical_phase >= 0
            AND theoretical_phase < 1
        )
);

CREATE TABLE measurement_results (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES qpe_experiments(experiment_id)
        ON DELETE CASCADE,
    shot_number INTEGER NOT NULL,
    measured_integer INTEGER NOT NULL,
    measured_phase NUMERIC(20,16) NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT measurement_shot_positive
        CHECK (shot_number >= 1),
    CONSTRAINT measurement_integer_nonnegative
        CHECK (measured_integer >= 0),
    CONSTRAINT measurement_phase_range
        CHECK (
            measured_phase >= 0
            AND measured_phase < 1
        ),
    CONSTRAINT measurement_unique_shot
        UNIQUE (experiment_id, shot_number)
);

CREATE INDEX idx_qpe_experiments_unitary
    ON qpe_experiments(unitary_id);

CREATE INDEX idx_probability_outcomes_experiment_probability
    ON probability_outcomes(experiment_id, probability DESC);

CREATE INDEX idx_measurement_results_experiment_outcome
    ON measurement_results(experiment_id, measured_integer);

CREATE OR REPLACE FUNCTION qpe_validate_estimate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_scale INTEGER;
BEGIN
    expected_scale := 2 ^ NEW.counting_qubits;

    IF NEW.estimated_integer IS NOT NULL
       AND (
           NEW.estimated_integer < 0
           OR NEW.estimated_integer >= expected_scale
       ) THEN
        RAISE EXCEPTION
            'Estimated integer % is outside [0, %)',
            NEW.estimated_integer,
            expected_scale;
    END IF;

    IF NEW.estimated_integer IS NOT NULL
       AND NEW.estimated_phase IS NULL THEN
        NEW.estimated_phase :=
            NEW.estimated_integer::NUMERIC
            / expected_scale;
    END IF;

    IF NEW.state = 'measured'
       AND NEW.estimated_integer IS NULL THEN
        RAISE EXCEPTION
            'A measured experiment requires an estimated outcome';
    END IF;

    IF NEW.state = 'measured'
       AND NEW.completed_at IS NULL THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_estimate
BEFORE INSERT OR UPDATE
ON qpe_experiments
FOR EACH ROW
EXECUTE FUNCTION qpe_validate_estimate();

CREATE OR REPLACE FUNCTION qpe_record_measurement(
    p_experiment_id BIGINT,
    p_shot_number INTEGER,
    p_measured_integer INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_qubits INTEGER;
    v_phase NUMERIC(20,16);
    v_scale INTEGER;
BEGIN
    SELECT counting_qubits
    INTO v_qubits
    FROM qpe_experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment % does not exist',
            p_experiment_id;
    END IF;

    v_scale := 2 ^ v_qubits;

    IF p_measured_integer < 0
       OR p_measured_integer >= v_scale THEN
        RAISE EXCEPTION
            'Outcome % is invalid for % counting qubits',
            p_measured_integer,
            v_qubits;
    END IF;

    SELECT
        p_measured_integer::NUMERIC / v_scale
    INTO v_phase;

    INSERT INTO measurement_results (
        experiment_id,
        shot_number,
        measured_integer,
        measured_phase
    )
    VALUES (
        p_experiment_id,
        p_shot_number,
        p_measured_integer,
        v_phase
    );
END;
$$;

CREATE OR REPLACE VIEW v_experiment_report AS
WITH dominant_outcome AS (
    SELECT
        experiment_id,
        outcome_integer,
        probability,
        ROW_NUMBER() OVER (
            PARTITION BY experiment_id
            ORDER BY probability DESC, outcome_integer
        ) AS rank_no
    FROM probability_outcomes
)
SELECT
    e.experiment_id,
    e.experiment_name,
    u.unitary_name,
    u.eigenphase AS target_phase,
    e.counting_qubits,
    e.shots,
    e.state,
    d.outcome_integer AS dominant_integer,
    d.outcome_integer::NUMERIC /
        (2 ^ e.counting_qubits) AS dominant_phase,
    d.probability AS dominant_probability,
    ABS(
        u.eigenphase
        - d.outcome_integer::NUMERIC /
          (2 ^ e.counting_qubits)
    ) AS absolute_phase_error
FROM qpe_experiments e
JOIN phase_unitaries u
    ON u.unitary_id = e.unitary_id
LEFT JOIN dominant_outcome d
    ON d.experiment_id = e.experiment_id
   AND d.rank_no = 1;

-- Phase gates have eigenvalue exp(2*pi*i*theta). These records use theta,
-- not the complex eigenvalue itself, because SQL is storing experimental
-- metadata and reproducible theoretical expectations.
INSERT INTO phase_unitaries (
    unitary_name,
    description,
    eigenphase,
    eigenstate_label
)
VALUES
(
    'P_5_8',
    'Single-qubit phase unitary with exactly representable binary phase',
    0.625,
    '|1>'
),
(
    'P_37_100',
    'Single-qubit phase unitary whose phase is not exactly represented by five bits',
    0.37,
    '|1>'
),
(
    'P_5_16',
    'Single-qubit phase unitary with phase 5/16',
    0.3125,
    '|1>'
);

INSERT INTO qpe_experiments (
    unitary_id,
    experiment_name,
    counting_qubits,
    shots,
    state
)
SELECT
    unitary_id,
    'exact_4_qubit',
    4,
    1000,
    'prepared'
FROM phase_unitaries
WHERE unitary_name = 'P_5_8';

INSERT INTO qpe_experiments (
    unitary_id,
    experiment_name,
    counting_qubits,
    shots,
    state
)
SELECT
    unitary_id,
    'approximate_5_qubit',
    5,
    2000,
    'prepared'
FROM phase_unitaries
WHERE unitary_name = 'P_37_100';

INSERT INTO qpe_experiments (
    unitary_id,
    experiment_name,
    counting_qubits,
    shots,
    state
)
SELECT
    unitary_id,
    'precision_5_qubit',
    5,
    2000,
    'prepared'
FROM phase_unitaries
WHERE unitary_name = 'P_5_16';

-- Controlled-U powers use exponent 2^k. The least significant control
-- corresponds to U^1, followed by U^2, U^4, and so on.
INSERT INTO qpe_operations (
    experiment_id,
    sequence_no,
    operation_type,
    control_qubit,
    power_exponent,
    phase_argument
)
SELECT
    e.experiment_id,
    k + 1,
    'CONTROLLED_U_POWER',
    k,
    2 ^ k,
    u.eigenphase * (2 ^ k)
FROM qpe_experiments e
JOIN phase_unitaries u
    ON u.unitary_id = e.unitary_id
CROSS JOIN LATERAL generate_series(
    0,
    e.counting_qubits - 1
) AS generated(k);

INSERT INTO qpe_operations (
    experiment_id,
    sequence_no,
    operation_type
)
SELECT
    experiment_id,
    counting_qubits + 1,
    'INVERSE_QFT'
FROM qpe_experiments;

-- Complete the two main examples.
UPDATE qpe_experiments
SET
    state = 'measured',
    estimated_integer = 10
WHERE experiment_name = 'exact_4_qubit';

UPDATE qpe_experiments
SET
    state = 'measured',
    estimated_integer = 12
WHERE experiment_name = 'approximate_5_qubit';

UPDATE qpe_experiments
SET
    state = 'measured',
    estimated_integer = 10
WHERE experiment_name = 'precision_5_qubit';

-- The probability distribution for an m-bit QPE register is:
--
--   p(y) = (1 / N^2) *
--          |sum_{k=0}^{N-1} exp(2*pi*i*k*(theta-y/N))|^2
--
-- PostgreSQL does not need complex-number support for this report. The
-- equivalent closed form uses sin ratios. The theta values below are
-- deliberately small enough to make numerical handling stable.
CREATE OR REPLACE FUNCTION qpe_theoretical_probability(
    p_theta NUMERIC,
    p_qubits INTEGER,
    p_outcome INTEGER
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    n NUMERIC;
    delta NUMERIC;
    numerator NUMERIC;
    denominator NUMERIC;
    probability NUMERIC;
BEGIN
    IF p_theta < 0 OR p_theta >= 1 THEN
        RAISE EXCEPTION 'theta must satisfy 0 <= theta < 1';
    END IF;

    IF p_qubits < 1 OR p_qubits > 20 THEN
        RAISE EXCEPTION 'qubit count must be between 1 and 20';
    END IF;

    n := (2 ^ p_qubits)::NUMERIC;

    IF p_outcome < 0 OR p_outcome >= n THEN
        RAISE EXCEPTION 'outcome outside counting-register range';
    END IF;

    delta := p_theta - p_outcome / n;

    IF abs(delta) < 0.000000000000001 THEN
        RETURN 1.0;
    END IF;

    numerator := sin(pi() * n * delta);
    denominator := sin(pi() * delta);

    probability :=
        (numerator / denominator) ^ 2 / (n ^ 2);

    RETURN LEAST(1.0, GREATEST(0.0, probability));
END;
$$;

-- Populate theoretical distributions for the approximate experiment.
INSERT INTO probability_outcomes (
    experiment_id,
    outcome_integer,
    probability,
    theoretical_phase
)
SELECT
    e.experiment_id,
    outcome,
    qpe_theoretical_probability(
        u.eigenphase,
        e.counting_qubits,
        outcome
    ),
    outcome::NUMERIC / (2 ^ e.counting_qubits)
FROM qpe_experiments e
JOIN phase_unitaries u
    ON u.unitary_id = e.unitary_id
CROSS JOIN LATERAL generate_series(
    0,
    (2 ^ e.counting_qubits) - 1
) AS generated(outcome);

-- Example deterministic measurements. In a real run these rows would be
-- inserted from measured circuit shots rather than assumed values.
BEGIN;

SELECT qpe_record_measurement(
    e.experiment_id,
    1,
    e.estimated_integer
)
FROM qpe_experiments e
WHERE e.experiment_name = 'exact_4_qubit';

SELECT qpe_record_measurement(
    e.experiment_id,
    1,
    e.estimated_integer
)
FROM qpe_experiments e
WHERE e.experiment_name = 'approximate_5_qubit';

COMMIT;

-- Query the most probable theoretical outcomes.
SELECT
    e.experiment_name,
    u.eigenphase AS target_phase,
    p.outcome_integer,
    p.theoretical_phase,
    p.probability
FROM qpe_experiments e
JOIN phase_unitaries u
    ON u.unitary_id = e.unitary_id
JOIN probability_outcomes p
    ON p.experiment_id = e.experiment_id
WHERE p.probability > 0.01
ORDER BY
    e.experiment_name,
    p.probability DESC,
    p.outcome_integer;

-- Aggregate measured outcomes into empirical frequencies.
SELECT
    e.experiment_name,
    m.measured_integer,
    m.measured_phase,
    COUNT(*) AS shots_observed,
    COUNT(*)::NUMERIC / e.shots AS empirical_fraction
FROM qpe_experiments e
JOIN measurement_results m
    ON m.experiment_id = e.experiment_id
GROUP BY
    e.experiment_name,
    e.shots,
    m.measured_integer,
    m.measured_phase
ORDER BY
    e.experiment_name,
    m.measured_integer;

-- CTE-based comparison of target phase and selected QPE estimate.
WITH experiment_accuracy AS (
    SELECT
        experiment_id,
        experiment_name,
        target_phase,
        dominant_phase,
        absolute_phase_error
    FROM v_experiment_report
)
SELECT
    experiment_name,
    target_phase,
    dominant_phase,
    absolute_phase_error,
    CASE
        WHEN absolute_phase_error = 0 THEN 'exact grid representation'
        WHEN absolute_phase_error <= 1.0 / (2 ^ 4)
            THEN 'within four-bit resolution'
        ELSE 'coarser approximation'
    END AS interpretation
FROM experiment_accuracy
ORDER BY absolute_phase_error;

-- Demonstrate a failed integrity operation. PostgreSQL rejects an invalid
-- outcome because the function checks the counting-register range.
DO $$
DECLARE
    experiment_key BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_key
    FROM qpe_experiments
    WHERE experiment_name = 'exact_4_qubit';

    BEGIN
        PERFORM qpe_record_measurement(
            experiment_key,
            2,
            16
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected invalid-measurement failure: %',
                SQLERRM;
    END;
END;
$$;

-- Final report includes target phase, dominant QPE outcome, resolution,
-- and error. Branching to a finer counting register reduces the phase-grid
-- spacing from 1/2^m to 1/2^(m+1), but increases simulation state size.
SELECT
    experiment_name,
    unitary_name,
    target_phase,
    counting_qubits,
    shots,
    state,
    dominant_integer,
    dominant_phase,
    dominant_probability,
    absolute_phase_error,
    1.0 / (2 ^ counting_qubits) AS phase_grid_spacing
FROM v_experiment_report
ORDER BY experiment_id;
