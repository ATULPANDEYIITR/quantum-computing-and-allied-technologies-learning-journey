-- PostgreSQL 15+
-- Relational model for quantum measurement experiments.
-- Stores theoretical probabilities separately from observed shot counts.
-- The database records experimental data; application code performs sampling.

BEGIN;

DROP VIEW IF EXISTS measurement_probability_report;
DROP TABLE IF EXISTS measurement_counts;
DROP TABLE IF EXISTS measurement_runs;
DROP TABLE IF EXISTS quantum_outcomes;
DROP TABLE IF EXISTS prepared_states;
DROP TABLE IF EXISTS quantum_experiments;

CREATE TABLE quantum_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(experiment_name)) > 0)
);

CREATE TABLE prepared_states (
    state_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id) ON DELETE CASCADE,
    state_name TEXT NOT NULL,
    register_width INTEGER NOT NULL CHECK (register_width > 0),
    CHECK (length(trim(state_name)) > 0),
    UNIQUE (experiment_id, state_name),
    UNIQUE (state_id, register_width)
);

CREATE TABLE quantum_outcomes (
    outcome_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_id BIGINT NOT NULL
        REFERENCES prepared_states(state_id) ON DELETE CASCADE,
    bitstring TEXT NOT NULL,
    theoretical_probability NUMERIC(18, 12) NOT NULL
        CHECK (
            theoretical_probability >= 0
            AND theoretical_probability <= 1
        ),
    CHECK (bitstring ~ '^[01]+$'),
    UNIQUE (state_id, bitstring)
);

CREATE TABLE measurement_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_id BIGINT NOT NULL
        REFERENCES prepared_states(state_id),
    run_label TEXT NOT NULL,
    shots INTEGER NOT NULL CHECK (shots > 0),
    random_seed BIGINT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'failed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,
    CHECK (
        (status = 'completed' AND completed_at IS NOT NULL
            AND failure_reason IS NULL)
        OR (status = 'failed' AND completed_at IS NOT NULL
            AND failure_reason IS NOT NULL)
        OR (status = 'pending' AND completed_at IS NULL
            AND failure_reason IS NULL)
    ),
    UNIQUE (state_id, run_label)
);

CREATE TABLE measurement_counts (
    run_id BIGINT NOT NULL
        REFERENCES measurement_runs(run_id) ON DELETE CASCADE,
    outcome_id BIGINT NOT NULL
        REFERENCES quantum_outcomes(outcome_id),
    observed_count INTEGER NOT NULL CHECK (observed_count >= 0),
    PRIMARY KEY (run_id, outcome_id)
);

CREATE INDEX idx_runs_state_status
    ON measurement_runs(state_id, status, started_at DESC);

CREATE INDEX idx_counts_outcome
    ON measurement_counts(outcome_id);

-- A trigger prevents a run from using an outcome belonging to another state.
CREATE OR REPLACE FUNCTION enforce_run_outcome_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    run_state BIGINT;
    outcome_state BIGINT;
BEGIN
    SELECT state_id
      INTO run_state
      FROM measurement_runs
     WHERE run_id = NEW.run_id;

    SELECT state_id
      INTO outcome_state
      FROM quantum_outcomes
     WHERE outcome_id = NEW.outcome_id;

    IF run_state IS NULL OR outcome_state IS NULL THEN
        RAISE EXCEPTION 'Run or outcome does not exist';
    END IF;

    IF run_state <> outcome_state THEN
        RAISE EXCEPTION
            'Outcome state % does not match run state %',
            outcome_state, run_state;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_run_outcome_state
BEFORE INSERT OR UPDATE ON measurement_counts
FOR EACH ROW EXECUTE FUNCTION enforce_run_outcome_state();

-- Cross-row probability totals and count totals cannot be enforced by ordinary
-- CHECK constraints. This deferred constraint trigger validates the probability
-- distribution at transaction commit, allowing all outcomes to be inserted
-- within one transaction.
CREATE OR REPLACE FUNCTION enforce_probability_normalization()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    affected_state BIGINT;
    probability_total NUMERIC;
    expected_outcomes INTEGER;
    valid_width INTEGER;
BEGIN
    affected_state := COALESCE(NEW.state_id, OLD.state_id);

    SELECT register_width
      INTO valid_width
      FROM prepared_states
     WHERE state_id = affected_state;

    IF valid_width IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*), COALESCE(SUM(theoretical_probability), 0)
      INTO expected_outcomes, probability_total
      FROM quantum_outcomes
     WHERE state_id = affected_state;

    IF expected_outcomes = 0 THEN
        RAISE EXCEPTION 'State % has no outcomes', affected_state;
    END IF;

    IF EXISTS (
        SELECT 1
          FROM quantum_outcomes
         WHERE state_id = affected_state
           AND length(bitstring) <> valid_width
    ) THEN
        RAISE EXCEPTION
            'Outcome width does not match state % register width',
            affected_state;
    END IF;

    IF ABS(probability_total - 1) > 0.000000001 THEN
        RAISE EXCEPTION
            'State % probabilities sum to %, not one',
            affected_state, probability_total;
    END IF;

    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_probability_normalization
AFTER INSERT OR UPDATE OR DELETE ON quantum_outcomes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_probability_normalization();

-- Validate the sum of counts when a run is marked completed. The check is
-- intentionally deferred until the state transition, so individual outcome
-- counts can be inserted incrementally within the same transaction.
CREATE OR REPLACE FUNCTION enforce_completed_run_counts()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total_count BIGINT;
    expected_shots INTEGER;
    number_of_outcomes INTEGER;
    number_of_count_rows INTEGER;
BEGIN
    IF NEW.status <> 'completed' THEN
        RETURN NEW;
    END IF;

    SELECT shots
      INTO expected_shots
      FROM measurement_runs
     WHERE run_id = NEW.run_id;

    SELECT COUNT(*), COALESCE(SUM(observed_count), 0)
      INTO number_of_count_rows, total_count
      FROM measurement_counts
     WHERE run_id = NEW.run_id;

    SELECT COUNT(*)
      INTO number_of_outcomes
      FROM quantum_outcomes
     WHERE state_id = NEW.state_id;

    IF number_of_count_rows <> number_of_outcomes THEN
        RAISE EXCEPTION
            'Completed run % must record every possible outcome',
            NEW.run_id;
    END IF;

    IF total_count <> expected_shots THEN
        RAISE EXCEPTION
            'Run % has % counts but declares % shots',
            NEW.run_id, total_count, expected_shots;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_completed_run_counts
BEFORE UPDATE OF status ON measurement_runs
FOR EACH ROW EXECUTE FUNCTION enforce_completed_run_counts();

-- Report observed frequencies alongside Born-rule probabilities.
CREATE VIEW measurement_probability_report AS
SELECT
    r.run_id,
    e.experiment_name,
    s.state_name,
    r.run_label,
    r.shots,
    o.bitstring,
    o.theoretical_probability,
    c.observed_count,
    c.observed_count::NUMERIC / r.shots AS observed_probability,
    SQRT(
        (
            (c.observed_count::NUMERIC / r.shots)
            * (1 - c.observed_count::NUMERIC / r.shots)
        ) / r.shots
    ) AS estimated_standard_error
FROM measurement_runs AS r
JOIN prepared_states AS s ON s.state_id = r.state_id
JOIN quantum_experiments AS e ON e.experiment_id = s.experiment_id
JOIN quantum_outcomes AS o ON o.state_id = s.state_id
JOIN measurement_counts AS c
  ON c.run_id = r.run_id AND c.outcome_id = o.outcome_id
WHERE r.status = 'completed';

-- Demonstration data: balanced qubit and correlated two-qubit Bell state.
INSERT INTO quantum_experiments (experiment_name, description)
VALUES
    ('balanced-qubit', 'Computational-basis measurement of a balanced qubit'),
    ('bell-correlation', 'Computational-basis measurement of a Bell state');

INSERT INTO prepared_states
    (experiment_id, state_name, register_width)
SELECT experiment_id, 'hadamard-state', 1
FROM quantum_experiments
WHERE experiment_name = 'balanced-qubit';

INSERT INTO prepared_states
    (experiment_id, state_name, register_width)
SELECT experiment_id, 'bell-state', 2
FROM quantum_experiments
WHERE experiment_name = 'bell-correlation';

INSERT INTO quantum_outcomes (state_id, bitstring, theoretical_probability)
SELECT state_id, outcome, probability
FROM prepared_states
CROSS JOIN (
    VALUES ('0', 0.5::NUMERIC), ('1', 0.5::NUMERIC)
) AS outcomes(outcome, probability)
WHERE state_name = 'hadamard-state';

INSERT INTO quantum_outcomes (state_id, bitstring, theoretical_probability)
SELECT state_id, outcome, probability
FROM prepared_states
CROSS JOIN (
    VALUES
        ('00', 0.5::NUMERIC),
        ('01', 0.0::NUMERIC),
        ('10', 0.0::NUMERIC),
        ('11', 0.5::NUMERIC)
) AS outcomes(outcome, probability)
WHERE state_name = 'bell-state';

INSERT INTO measurement_runs
    (state_id, run_label, shots, random_seed, status)
SELECT state_id, 'calibration-1000', 1000, 42, 'pending'
FROM prepared_states
WHERE state_name = 'hadamard-state';

INSERT INTO measurement_runs
    (state_id, run_label, shots, random_seed, status)
SELECT state_id, 'correlation-2000', 2000, 77, 'pending'
FROM prepared_states
WHERE state_name = 'bell-state';

-- Insert simulated counts. These are example observations, not hardware data.
INSERT INTO measurement_counts (run_id, outcome_id, observed_count)
SELECT r.run_id, o.outcome_id,
       CASE o.bitstring
           WHEN '0' THEN 503
           WHEN '1' THEN 497
       END
FROM measurement_runs AS r
JOIN prepared_states AS s ON s.state_id = r.state_id
JOIN quantum_outcomes AS o ON o.state_id = s.state_id
WHERE r.run_label = 'calibration-1000';

INSERT INTO measurement_counts (run_id, outcome_id, observed_count)
SELECT r.run_id, o.outcome_id,
       CASE o.bitstring
           WHEN '00' THEN 1007
           WHEN '01' THEN 0
           WHEN '10' THEN 0
           WHEN '11' THEN 993
       END
FROM measurement_runs AS r
JOIN prepared_states AS s ON s.state_id = r.state_id
JOIN quantum_outcomes AS o ON o.state_id = s.state_id
WHERE r.run_label = 'correlation-2000';

UPDATE measurement_runs
SET status = 'completed', completed_at = CURRENT_TIMESTAMP
WHERE run_label IN ('calibration-1000', 'correlation-2000');

COMMIT;

-- Per-outcome comparison of expected and observed probabilities.
SELECT
    experiment_name,
    state_name,
    run_label,
    shots,
    bitstring,
    theoretical_probability,
    observed_count,
    ROUND(observed_probability, 4) AS observed_probability,
    ROUND(estimated_standard_error, 4) AS estimated_standard_error
FROM measurement_probability_report
ORDER BY experiment_name, bitstring;

-- Aggregate total variation distance. A lower value means that the empirical
-- distribution is closer to the theoretical distribution for this run.
SELECT
    run_id,
    experiment_name,
    run_label,
    MAX(shots) AS shots,
    ROUND(
        SUM(ABS(observed_probability - theoretical_probability)) / 2,
        4
    ) AS total_variation_distance
FROM measurement_probability_report
GROUP BY run_id, experiment_name, run_label
ORDER BY run_id;

-- Detect impossible outcomes in the Bell-state experiment.
SELECT run_label, bitstring, observed_count
FROM measurement_probability_report
WHERE state_name = 'bell-state'
  AND theoretical_probability = 0
  AND observed_count > 0;

-- Audit incomplete or failed experiments separately from completed results.
SELECT run_id, run_label, status, failure_reason
FROM measurement_runs
WHERE status <> 'completed'
ORDER BY started_at DESC;
