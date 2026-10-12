-- Quantum simulator experiment registry and execution ledger.
-- PostgreSQL 15+.
--
-- The schema separates immutable circuit definitions, exact statevector
-- predictions, and finite shot-based observations. A shot result is not
-- treated as identical to its theoretical probability.

BEGIN;

DROP SCHEMA IF EXISTS quantum_lab CASCADE;
CREATE SCHEMA quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TYPE simulation_mode AS ENUM (
    'statevector',
    'shot_based'
);

CREATE TYPE job_status AS ENUM (
    'created',
    'validated',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE experiment_status AS ENUM (
    'draft',
    'approved',
    'retired'
);

CREATE TABLE quantum_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name TEXT NOT NULL UNIQUE,
    purpose TEXT NOT NULL,
    status experiment_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(experiment_name)) > 0),
    CHECK (length(trim(purpose)) > 0)
);

CREATE TABLE circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id),
    circuit_name TEXT NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (qubit_count BETWEEN 1 AND 24),
    gate_count INTEGER NOT NULL CHECK (gate_count >= 0),
    measurement_qubits INTEGER[] NOT NULL,
    circuit_description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (experiment_id, circuit_name),
    CHECK (cardinality(measurement_qubits) BETWEEN 1 AND qubit_count),
    CHECK (
        array_position(measurement_qubits, NULL) IS NULL
    ),
    CHECK (
        (
            SELECT COUNT(*) = COUNT(DISTINCT q)
            FROM unnest(measurement_qubits) AS q
        )
    )
);

-- Validate selected measurement qubits against the circuit's qubit count.
CREATE FUNCTION validate_measurement_qubits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_qubit INTEGER;
BEGIN
    FOREACH selected_qubit IN ARRAY NEW.measurement_qubits LOOP
        IF selected_qubit < 0 OR selected_qubit >= NEW.qubit_count THEN
            RAISE EXCEPTION
                'Measurement qubit % is invalid for a %-qubit circuit',
                selected_qubit, NEW.qubit_count;
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER circuits_validate_measurements
BEFORE INSERT OR UPDATE OF measurement_qubits, qubit_count
ON circuits
FOR EACH ROW
EXECUTE FUNCTION validate_measurement_qubits();

CREATE TABLE circuit_gates (
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    gate_position INTEGER NOT NULL CHECK (gate_position >= 0),
    gate_name TEXT NOT NULL,
    target_qubit INTEGER NOT NULL CHECK (target_qubit >= 0),
    control_qubit INTEGER,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (circuit_id, gate_position),
    CHECK (length(trim(gate_name)) > 0),
    CHECK (control_qubit IS NULL OR control_qubit >= 0),
    CHECK (control_qubit IS NULL OR control_qubit <> target_qubit),
    CHECK (jsonb_typeof(parameters) = 'object')
);

CREATE FUNCTION validate_gate_qubits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    circuit_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO circuit_qubits
    FROM circuits
    WHERE circuit_id = NEW.circuit_id
    FOR KEY SHARE;

    IF circuit_qubits IS NULL THEN
        RAISE EXCEPTION 'Circuit % does not exist', NEW.circuit_id;
    END IF;

    IF NEW.target_qubit >= circuit_qubits THEN
        RAISE EXCEPTION 'Target qubit % exceeds circuit width',
            NEW.target_qubit;
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND NEW.control_qubit >= circuit_qubits THEN
        RAISE EXCEPTION 'Control qubit % exceeds circuit width',
            NEW.control_qubit;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER circuit_gates_validate
BEFORE INSERT OR UPDATE ON circuit_gates
FOR EACH ROW
EXECUTE FUNCTION validate_gate_qubits();

CREATE TABLE simulation_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id),
    mode simulation_mode NOT NULL,
    status job_status NOT NULL DEFAULT 'created',
    shots BIGINT NOT NULL DEFAULT 0,
    random_seed BIGINT NOT NULL DEFAULT 0,
    requested_by TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,
    CHECK (shots >= 0),
    CHECK (
        (mode = 'statevector' AND shots = 0)
        OR
        (mode = 'shot_based' AND shots BETWEEN 1 AND 10000000)
    ),
    CHECK (
        (status = 'failed' AND failure_reason IS NOT NULL)
        OR
        (status <> 'failed')
    ),
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    ),
    CHECK (
        status NOT IN ('completed', 'failed', 'cancelled')
        OR completed_at IS NOT NULL
    ),
    CHECK (length(trim(requested_by)) > 0)
);

CREATE INDEX simulation_jobs_status_submitted_idx
    ON simulation_jobs(status, submitted_at DESC);

CREATE INDEX simulation_jobs_circuit_idx
    ON simulation_jobs(circuit_id, submitted_at DESC);

CREATE TABLE exact_outcomes (
    job_id BIGINT NOT NULL REFERENCES simulation_jobs(job_id)
        ON DELETE CASCADE,
    outcome TEXT NOT NULL,
    probability DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (job_id, outcome),
    CHECK (outcome ~ '^[01]+$'),
    CHECK (
        probability >= 0.0
        AND probability <= 1.0
        AND probability <> 'NaN'::DOUBLE PRECISION
        AND probability <> 'Infinity'::DOUBLE PRECISION
    )
);

CREATE TABLE observed_counts (
    job_id BIGINT NOT NULL REFERENCES simulation_jobs(job_id)
        ON DELETE CASCADE,
    outcome TEXT NOT NULL,
    count BIGINT NOT NULL CHECK (count >= 0),
    PRIMARY KEY (job_id, outcome),
    CHECK (outcome ~ '^[01]+$')
);

CREATE TABLE execution_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES simulation_jobs(job_id)
        ON DELETE CASCADE,
    previous_status job_status,
    new_status job_status NOT NULL,
    event_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(event_detail) = 'object')
);

CREATE FUNCTION enforce_job_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('completed', 'failed', 'cancelled')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION
            'Terminal job status % cannot transition to %',
            OLD.status, NEW.status;
    END IF;

    IF NEW.status = 'running' AND OLD.status NOT IN ('created', 'validated') THEN
        RAISE EXCEPTION 'Job can start only from created or validated';
    END IF;

    IF NEW.status = 'completed' AND OLD.status <> 'running' THEN
        RAISE EXCEPTION 'Only running jobs can complete';
    END IF;

    IF NEW.status = 'failed' AND OLD.status NOT IN (
        'created', 'validated', 'running'
    ) THEN
        RAISE EXCEPTION 'Invalid failure transition';
    END IF;

    IF NEW.status = 'cancelled' AND OLD.status IN (
        'completed', 'failed', 'cancelled'
    ) THEN
        RAISE EXCEPTION 'Terminal job cannot be cancelled';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER simulation_jobs_transition
BEFORE UPDATE OF status ON simulation_jobs
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION enforce_job_transition();

CREATE FUNCTION record_job_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO execution_events (
        job_id,
        previous_status,
        new_status,
        event_detail
    )
    VALUES (
        NEW.job_id,
        OLD.status,
        NEW.status,
        jsonb_build_object(
            'mode', NEW.mode,
            'shots', NEW.shots
        )
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER simulation_jobs_audit
AFTER UPDATE OF status ON simulation_jobs
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION record_job_transition();

-- The total of exact probabilities must equal one for a completed job.
-- Cross-row sums cannot be enforced with a normal CHECK constraint, so
-- validation is performed by a transaction-safe finalization function.
CREATE FUNCTION finalize_simulation_job(p_job_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    job_record simulation_jobs%ROWTYPE;
    outcome_total DOUBLE PRECISION;
    count_total BIGINT;
    expected_width INTEGER;
BEGIN
    SELECT j.*
    INTO job_record
    FROM simulation_jobs AS j
    WHERE j.job_id = p_job_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown simulation job %', p_job_id;
    END IF;

    IF job_record.status <> 'running' THEN
        RAISE EXCEPTION 'Only running jobs can be finalized';
    END IF;

    SELECT cardinality(c.measurement_qubits)
    INTO expected_width
    FROM circuits AS c
    WHERE c.circuit_id = job_record.circuit_id;

    SELECT COALESCE(SUM(probability), 0.0)
    INTO outcome_total
    FROM exact_outcomes
    WHERE job_id = p_job_id;

    IF ABS(outcome_total - 1.0) > 1e-8 THEN
        RAISE EXCEPTION
            'Exact probabilities sum to %, expected one',
            outcome_total;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM exact_outcomes
        WHERE job_id = p_job_id
          AND length(outcome) <> expected_width
    ) THEN
        RAISE EXCEPTION 'Outcome width does not match measurement width';
    END IF;

    IF job_record.mode = 'shot_based' THEN
        SELECT COALESCE(SUM(count), 0)
        INTO count_total
        FROM observed_counts
        WHERE job_id = p_job_id;

        IF count_total <> job_record.shots THEN
            RAISE EXCEPTION
                'Observed count total % does not equal requested shots %',
                count_total, job_record.shots;
        END IF;

        IF EXISTS (
            SELECT 1
            FROM observed_counts
            WHERE job_id = p_job_id
              AND length(outcome) <> expected_width
        ) THEN
            RAISE EXCEPTION 'Observed outcome width is invalid';
        END IF;
    ELSIF EXISTS (
        SELECT 1 FROM observed_counts WHERE job_id = p_job_id
    ) THEN
        RAISE EXCEPTION 'Statevector jobs must not contain shot counts';
    END IF;

    UPDATE simulation_jobs
    SET status = 'completed',
        completed_at = CURRENT_TIMESTAMP
    WHERE job_id = p_job_id;
END;
$$;

INSERT INTO quantum_experiments (
    experiment_name, purpose, status
)
VALUES
(
    'bell_entanglement',
    'Compare ideal Bell-state probabilities with finite measurements',
    'approved'
),
(
    'ghz_correlations',
    'Validate correlated outcomes in a five-qubit GHZ experiment',
    'approved'
),
(
    'phase_interference',
    'Measure interference after a phase shift between Hadamard gates',
    'approved'
);

INSERT INTO circuits (
    experiment_id,
    circuit_name,
    qubit_count,
    gate_count,
    measurement_qubits,
    circuit_description
)
SELECT
    experiment_id,
    'bell_pair',
    2,
    2,
    ARRAY[0, 1],
    'Hadamard on qubit zero followed by controlled X'
FROM quantum_experiments
WHERE experiment_name = 'bell_entanglement';

INSERT INTO circuits (
    experiment_id,
    circuit_name,
    qubit_count,
    gate_count,
    measurement_qubits,
    circuit_description
)
SELECT
    experiment_id,
    'ghz_five',
    5,
    5,
    ARRAY[0, 1, 2, 3, 4],
    'Hadamard on qubit zero and four controlled-X gates'
FROM quantum_experiments
WHERE experiment_name = 'ghz_correlations';

INSERT INTO circuits (
    experiment_id,
    circuit_name,
    qubit_count,
    gate_count,
    measurement_qubits,
    circuit_description
)
SELECT
    experiment_id,
    'phase_flip',
    1,
    3,
    ARRAY[0],
    'Hadamard, phase pi, Hadamard'
FROM quantum_experiments
WHERE experiment_name = 'phase_interference';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 0, 'H', 0, NULL, '{}'::jsonb
FROM circuits WHERE circuit_name = 'bell_pair';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 1, 'CX', 1, 0, '{}'::jsonb
FROM circuits WHERE circuit_name = 'bell_pair';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 0, 'H', 0, NULL, '{}'::jsonb
FROM circuits WHERE circuit_name = 'ghz_five';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT
    circuit_id,
    target_qubit,
    'CX',
    target_qubit,
    0,
    '{}'::jsonb
FROM circuits
CROSS JOIN generate_series(1, 4) AS target_qubit
WHERE circuit_name = 'ghz_five';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 0, 'H', 0, NULL, '{}'::jsonb
FROM circuits WHERE circuit_name = 'phase_flip';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 1, 'P', 0, NULL, '{"theta": 3.141592653589793}'::jsonb
FROM circuits WHERE circuit_name = 'phase_flip';

INSERT INTO circuit_gates (
    circuit_id, gate_position, gate_name, target_qubit, control_qubit, parameters
)
SELECT circuit_id, 2, 'H', 0, NULL, '{}'::jsonb
FROM circuits WHERE circuit_name = 'phase_flip';

-- Seed one completed exact job and one completed shot-based job.
INSERT INTO simulation_jobs (
    circuit_id, mode, status, shots, random_seed, requested_by,
    started_at, completed_at
)
SELECT circuit_id, 'statevector', 'running', 0, 41, 'researcher',
       CURRENT_TIMESTAMP, NULL
FROM circuits
WHERE circuit_name = 'bell_pair';

INSERT INTO exact_outcomes (job_id, outcome, probability)
SELECT job_id, '00', 0.5 FROM simulation_jobs
WHERE requested_by = 'researcher' AND mode = 'statevector';

INSERT INTO exact_outcomes (job_id, outcome, probability)
SELECT job_id, '01', 0.0 FROM simulation_jobs
WHERE requested_by = 'researcher' AND mode = 'statevector';

INSERT INTO exact_outcomes (job_id, outcome, probability)
SELECT job_id, '10', 0.0 FROM simulation_jobs
WHERE requested_by = 'researcher' AND mode = 'statevector';

INSERT INTO exact_outcomes (job_id, outcome, probability)
SELECT job_id, '11', 0.5 FROM simulation_jobs
WHERE requested_by = 'researcher' AND mode = 'statevector';

SELECT finalize_simulation_job(job_id)
FROM simulation_jobs
WHERE requested_by = 'researcher' AND mode = 'statevector';

INSERT INTO simulation_jobs (
    circuit_id, mode, status, shots, random_seed, requested_by,
    started_at, completed_at
)
SELECT circuit_id, 'shot_based', 'running', 1000, 99, 'analyst',
       CURRENT_TIMESTAMP, NULL
FROM circuits
WHERE circuit_name = 'bell_pair';

INSERT INTO exact_outcomes (job_id, outcome, probability)
SELECT job_id, outcome, probability
FROM simulation_jobs
CROSS JOIN (
    VALUES ('00', 0.5::DOUBLE PRECISION),
           ('01', 0.0::DOUBLE PRECISION),
           ('10', 0.0::DOUBLE PRECISION),
           ('11', 0.5::DOUBLE PRECISION)
) AS expected(outcome, probability)
WHERE requested_by = 'analyst' AND mode = 'shot_based';

INSERT INTO observed_counts (job_id, outcome, count)
SELECT job_id, outcome, count
FROM simulation_jobs
CROSS JOIN (
    VALUES ('00', 492::BIGINT),
           ('01', 0::BIGINT),
           ('10', 0::BIGINT),
           ('11', 508::BIGINT)
) AS observed(outcome, count)
WHERE requested_by = 'analyst' AND mode = 'shot_based';

SELECT finalize_simulation_job(job_id)
FROM simulation_jobs
WHERE requested_by = 'analyst' AND mode = 'shot_based';

-- Exact versus empirical probabilities for the Bell experiment.
SELECT
    j.job_id,
    e.outcome,
    e.probability AS exact_probability,
    COALESCE(o.count, 0) AS observed_count,
    CASE
        WHEN j.mode = 'shot_based'
        THEN COALESCE(o.count, 0)::DOUBLE PRECISION / j.shots
        ELSE NULL
    END AS empirical_probability
FROM simulation_jobs AS j
JOIN exact_outcomes AS e ON e.job_id = j.job_id
LEFT JOIN observed_counts AS o
    ON o.job_id = e.job_id
   AND o.outcome = e.outcome
ORDER BY j.job_id, e.outcome;

-- Shot-level statistical comparison. A finite sample can differ from theory
-- even when the simulator is correct.
SELECT
    j.job_id,
    j.shots,
    SUM(o.count) AS total_observed_shots,
    SUM(
        ABS(e.probability - o.count::DOUBLE PRECISION / j.shots)
    ) / 2.0 AS total_variation_distance
FROM simulation_jobs AS j
JOIN exact_outcomes AS e ON e.job_id = j.job_id
JOIN observed_counts AS o
    ON o.job_id = e.job_id
   AND o.outcome = e.outcome
WHERE j.mode = 'shot_based'
  AND j.status = 'completed'
GROUP BY j.job_id, j.shots;

-- Circuit metadata and estimated dense-statevector storage.
SELECT
    circuit_name,
    qubit_count,
    gate_count,
    measurement_qubits,
    power(2::DOUBLE PRECISION, qubit_count) AS amplitude_count,
    power(2::DOUBLE PRECISION, qubit_count) * 16 / 1048576
        AS approximate_raw_mib
FROM circuits
ORDER BY qubit_count, circuit_name;

-- Job status history is derived from audited transitions.
SELECT
    e.job_id,
    e.previous_status,
    e.new_status,
    e.occurred_at,
    e.event_detail
FROM execution_events AS e
ORDER BY e.job_id, e.occurred_at;

-- The following examples are deliberately commented out because each should
-- fail and abort its statement:
--
-- Invalid statevector job with nonzero shots:
-- INSERT INTO simulation_jobs
--     (circuit_id, mode, shots, requested_by)
-- SELECT circuit_id, 'statevector', 100, 'invalid-client'
-- FROM circuits WHERE circuit_name = 'bell_pair';
--
-- Invalid target qubit:
-- INSERT INTO circuit_gates
--     (circuit_id, gate_position, gate_name, target_qubit)
-- SELECT circuit_id, 100, 'H', 99
-- FROM circuits WHERE circuit_name = 'bell_pair';
--
-- Invalid terminal transition:
-- UPDATE simulation_jobs
-- SET status = 'running'
-- WHERE status = 'completed';

COMMIT;
