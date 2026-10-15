-- PostgreSQL 15+ multi-qubit circuit laboratory.
-- This database models quantum experiments, circuit operations, validation
-- policies, execution runs, and measurement results. It complements the
-- state-vector programs by providing persistent provenance and auditability.

BEGIN;

DROP SCHEMA IF EXISTS quantum_lab CASCADE;
CREATE SCHEMA quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TYPE experiment_status AS ENUM (
    'draft', 'validated', 'executed', 'rejected'
);

CREATE TYPE gate_kind AS ENUM (
    'H', 'X', 'Y', 'Z', 'S', 'T', 'RX', 'RY', 'RZ', 'CX', 'CZ', 'MCX'
);

CREATE TYPE run_status AS ENUM (
    'queued', 'running', 'completed', 'failed'
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (username ~ '^[a-z][a-z0-9_-]{2,31}$'),
    CHECK (length(trim(full_name)) >= 2)
);

CREATE TABLE quantum_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id BIGINT NOT NULL REFERENCES researchers(researcher_id),
    experiment_name TEXT NOT NULL,
    description TEXT NOT NULL,
    qubit_count SMALLINT NOT NULL,
    status experiment_status NOT NULL DEFAULT 'draft',
    random_seed BIGINT NOT NULL DEFAULT 2026,
    maximum_operations INTEGER NOT NULL DEFAULT 1000,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMPTZ,
    CHECK (qubit_count BETWEEN 1 AND 20),
    CHECK (maximum_operations BETWEEN 0 AND 100000),
    CHECK (length(trim(experiment_name)) BETWEEN 3 AND 120),
    CHECK (
        (status = 'draft' AND validated_at IS NULL)
        OR (status <> 'draft' AND validated_at IS NOT NULL)
    ),
    UNIQUE (owner_id, experiment_name)
);

CREATE TABLE circuit_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    kind gate_kind NOT NULL,
    target_qubit SMALLINT NOT NULL,
    angle_radians DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (experiment_id, sequence_number),
    CHECK (sequence_number >= 0),
    CHECK (target_qubit >= 0),
    CHECK (
        (kind IN ('RX', 'RY', 'RZ') AND angle_radians IS NOT NULL)
        OR (kind NOT IN ('RX', 'RY', 'RZ') AND angle_radians IS NULL)
    ),
    CHECK (
        angle_radians IS NULL
        OR angle_radians BETWEEN -1000000 AND 1000000
    )
);

CREATE TABLE operation_controls (
    operation_id BIGINT NOT NULL
        REFERENCES circuit_operations(operation_id) ON DELETE CASCADE,
    control_qubit SMALLINT NOT NULL,
    PRIMARY KEY (operation_id, control_qubit),
    CHECK (control_qubit >= 0)
);

CREATE TABLE experiment_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name TEXT NOT NULL UNIQUE,
    maximum_qubits SMALLINT NOT NULL,
    maximum_operations INTEGER NOT NULL,
    require_controlled_gate BOOLEAN NOT NULL DEFAULT FALSE,
    require_completed_validation BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (maximum_qubits BETWEEN 1 AND 20),
    CHECK (maximum_operations >= 0)
);

CREATE TABLE experiment_validations (
    validation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id) ON DELETE CASCADE,
    policy_id BIGINT NOT NULL REFERENCES experiment_policies(policy_id),
    passed BOOLEAN NOT NULL,
    findings JSONB NOT NULL DEFAULT '[]'::jsonb,
    validated_by BIGINT NOT NULL REFERENCES researchers(researcher_id),
    validated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (jsonb_typeof(findings) = 'array')
);

CREATE TABLE execution_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id),
    submitted_by BIGINT NOT NULL REFERENCES researchers(researcher_id),
    status run_status NOT NULL DEFAULT 'queued',
    shots INTEGER NOT NULL,
    backend_name TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (shots BETWEEN 1 AND 1000000),
    CHECK (length(trim(backend_name)) BETWEEN 2 AND 100),
    CHECK (
        completed_at IS NULL OR
        (started_at IS NOT NULL AND completed_at >= started_at)
    ),
    CHECK (
        status <> 'failed' OR error_message IS NOT NULL
    )
);

CREATE TABLE measurement_results (
    run_id BIGINT NOT NULL
        REFERENCES execution_runs(run_id) ON DELETE CASCADE,
    bitstring TEXT NOT NULL,
    occurrences INTEGER NOT NULL,
    PRIMARY KEY (run_id, bitstring),
    CHECK (bitstring ~ '^[01]+$'),
    CHECK (occurrences > 0)
);

CREATE INDEX idx_experiments_owner_status
    ON quantum_experiments(owner_id, status);

CREATE INDEX idx_operations_experiment_order
    ON circuit_operations(experiment_id, sequence_number);

CREATE INDEX idx_validations_latest
    ON experiment_validations(experiment_id, validated_at DESC);

CREATE INDEX idx_runs_experiment_created
    ON execution_runs(experiment_id, created_at DESC);

CREATE INDEX idx_runs_status
    ON execution_runs(status) WHERE status IN ('queued', 'running');

CREATE OR REPLACE FUNCTION validate_operation_domain()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_qubit_count INTEGER;
    v_status experiment_status;
    v_operation_limit INTEGER;
    v_existing_count INTEGER;
BEGIN
    SELECT qubit_count, status, maximum_operations
    INTO v_qubit_count, v_status, v_operation_limit
    FROM quantum_experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment % does not exist', NEW.experiment_id;
    END IF;

    IF v_status <> 'draft' THEN
        RAISE EXCEPTION
            'Operations can only be added to draft experiments';
    END IF;

    IF NEW.target_qubit >= v_qubit_count THEN
        RAISE EXCEPTION
            'Target qubit % is invalid for a %-qubit circuit',
            NEW.target_qubit, v_qubit_count;
    END IF;

    SELECT count(*) INTO v_existing_count
    FROM circuit_operations
    WHERE experiment_id = NEW.experiment_id
      AND operation_id <> COALESCE(NEW.operation_id, -1);

    IF v_existing_count >= v_operation_limit THEN
        RAISE EXCEPTION 'Experiment operation budget exceeded';
    END IF;

    IF NEW.kind IN ('CX', 'CZ', 'MCX') THEN
        -- Controlled operations are checked for at least one control after
        -- the operation row exists, because controls use a separate relation.
        NULL;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_operation_domain
BEFORE INSERT OR UPDATE ON circuit_operations
FOR EACH ROW EXECUTE FUNCTION validate_operation_domain();

CREATE OR REPLACE FUNCTION validate_control_domain()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_target INTEGER;
    v_qubit_count INTEGER;
    v_kind gate_kind;
    v_status experiment_status;
BEGIN
    SELECT op.target_qubit, e.qubit_count, op.kind, e.status
    INTO v_target, v_qubit_count, v_kind, v_status
    FROM circuit_operations op
    JOIN quantum_experiments e USING (experiment_id)
    WHERE op.operation_id = NEW.operation_id
    FOR UPDATE OF e;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Operation % does not exist', NEW.operation_id;
    END IF;

    IF v_status <> 'draft' THEN
        RAISE EXCEPTION 'Controls cannot change after validation';
    END IF;

    IF NEW.control_qubit >= v_qubit_count THEN
        RAISE EXCEPTION 'Control qubit exceeds circuit width';
    END IF;

    IF NEW.control_qubit = v_target THEN
        RAISE EXCEPTION 'A gate cannot control itself';
    END IF;

    IF v_kind NOT IN ('CX', 'CZ', 'MCX') THEN
        RAISE EXCEPTION 'Gate % does not accept controls', v_kind;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_control_domain
BEFORE INSERT OR UPDATE ON operation_controls
FOR EACH ROW EXECUTE FUNCTION validate_control_domain();

CREATE OR REPLACE FUNCTION validate_experiment(
    p_experiment_id BIGINT,
    p_policy_id BIGINT,
    p_researcher_id BIGINT
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    e quantum_experiments%ROWTYPE;
    p experiment_policies%ROWTYPE;
    operation_count INTEGER;
    has_controlled_gate BOOLEAN;
    findings JSONB := '[]'::jsonb;
    passed BOOLEAN := TRUE;
BEGIN
    SELECT * INTO e
    FROM quantum_experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown experiment %', p_experiment_id;
    END IF;

    IF e.status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft experiments can be validated';
    END IF;

    SELECT * INTO p
    FROM experiment_policies
    WHERE policy_id = p_policy_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown policy %', p_policy_id;
    END IF;

    SELECT count(*) INTO operation_count
    FROM circuit_operations
    WHERE experiment_id = p_experiment_id;

    SELECT EXISTS (
        SELECT 1
        FROM circuit_operations op
        JOIN operation_controls c USING (operation_id)
        WHERE op.experiment_id = p_experiment_id
    ) INTO has_controlled_gate;

    IF e.qubit_count > p.maximum_qubits THEN
        findings := findings || jsonb_build_array(
            'Qubit count exceeds policy maximum'
        );
        passed := FALSE;
    END IF;

    IF operation_count > p.maximum_operations
       OR operation_count > e.maximum_operations THEN
        findings := findings || jsonb_build_array(
            'Operation count exceeds policy budget'
        );
        passed := FALSE;
    END IF;

    IF p.require_controlled_gate AND NOT has_controlled_gate THEN
        findings := findings || jsonb_build_array(
            'Policy requires at least one controlled gate'
        );
        passed := FALSE;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM circuit_operations op
        WHERE op.experiment_id = p_experiment_id
          AND op.kind IN ('CX', 'CZ', 'MCX')
          AND NOT EXISTS (
              SELECT 1
              FROM operation_controls c
              WHERE c.operation_id = op.operation_id
          )
    ) THEN
        findings := findings || jsonb_build_array(
            'A controlled gate has no control qubit'
        );
        passed := FALSE;
    END IF;

    INSERT INTO experiment_validations (
        experiment_id, policy_id, passed, findings, validated_by
    )
    VALUES (
        p_experiment_id, p_policy_id, passed, findings, p_researcher_id
    );

    UPDATE quantum_experiments
    SET status = CASE WHEN passed THEN 'validated'::experiment_status
                      ELSE 'rejected'::experiment_status END,
        validated_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id;

    RETURN jsonb_build_object(
        'passed', passed,
        'findings', findings,
        'operation_count', operation_count,
        'qubit_count', e.qubit_count
    );
END;
$$;

CREATE OR REPLACE FUNCTION guard_execution_run()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_status experiment_status;
    v_width INTEGER;
    v_validation_passed BOOLEAN;
BEGIN
    SELECT status, qubit_count
    INTO v_status, v_width
    FROM quantum_experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist';
    END IF;

    SELECT passed INTO v_validation_passed
    FROM experiment_validations
    WHERE experiment_id = NEW.experiment_id
    ORDER BY validated_at DESC, validation_id DESC
    LIMIT 1;

    IF v_status <> 'validated' OR v_validation_passed IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'Execution requires a passing validation';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM measurement_results mr
        JOIN execution_runs er USING (run_id)
        WHERE er.experiment_id = NEW.experiment_id
          AND length(mr.bitstring) <> v_width
    ) THEN
        RAISE EXCEPTION 'Existing measurement width is inconsistent';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_guard_execution_run
BEFORE INSERT ON execution_runs
FOR EACH ROW EXECUTE FUNCTION guard_execution_run();

CREATE OR REPLACE FUNCTION guard_measurement_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_width INTEGER;
    v_shots INTEGER;
    v_status run_status;
    total_existing BIGINT;
BEGIN
    SELECT e.qubit_count, r.shots, r.status
    INTO v_width, v_shots, v_status
    FROM execution_runs r
    JOIN quantum_experiments e USING (experiment_id)
    WHERE r.run_id = NEW.run_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Execution run does not exist';
    END IF;

    IF v_status <> 'running' THEN
        RAISE EXCEPTION 'Results can only be recorded for running jobs';
    END IF;

    IF length(NEW.bitstring) <> v_width THEN
        RAISE EXCEPTION 'Measurement width does not match circuit width';
    END IF;

    SELECT COALESCE(sum(occurrences), 0) INTO total_existing
    FROM measurement_results
    WHERE run_id = NEW.run_id
      AND (TG_OP <> 'UPDATE' OR bitstring <> OLD.bitstring);

    IF total_existing + NEW.occurrences > v_shots THEN
        RAISE EXCEPTION 'Measurement counts exceed requested shots';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_guard_measurement_result
BEFORE INSERT OR UPDATE ON measurement_results
FOR EACH ROW EXECUTE FUNCTION guard_measurement_result();

CREATE VIEW experiment_inventory AS
SELECT
    e.experiment_id,
    e.experiment_name,
    r.username AS owner,
    e.qubit_count,
    e.status,
    count(DISTINCT op.operation_id) AS operation_count,
    count(DISTINCT v.validation_id) AS validation_count,
    max(v.passed) FILTER (
        WHERE v.validated_at = (
            SELECT max(v2.validated_at)
            FROM experiment_validations v2
            WHERE v2.experiment_id = e.experiment_id
        )
    ) AS latest_validation_passed
FROM quantum_experiments e
JOIN researchers r ON r.researcher_id = e.owner_id
LEFT JOIN circuit_operations op USING (experiment_id)
LEFT JOIN experiment_validations v USING (experiment_id)
GROUP BY e.experiment_id, e.experiment_name, r.username,
         e.qubit_count, e.status;

CREATE VIEW execution_measurement_summary AS
SELECT
    run.run_id,
    run.experiment_id,
    run.backend_name,
    run.shots,
    run.status,
    COALESCE(sum(result.occurrences), 0) AS recorded_shots,
    CASE
        WHEN run.status = 'completed' AND run.shots > 0
        THEN COALESCE(sum(result.occurrences), 0)::numeric / run.shots
        ELSE NULL
    END AS recorded_fraction
FROM execution_runs run
LEFT JOIN measurement_results result USING (run_id)
GROUP BY run.run_id, run.experiment_id, run.backend_name,
         run.shots, run.status;

INSERT INTO researchers (username, full_name)
VALUES
    ('atul_quantum', 'Atul Pandey'),
    ('researcher_ada', 'Ada Researcher');

INSERT INTO experiment_policies (
    policy_name, maximum_qubits, maximum_operations,
    require_controlled_gate
)
VALUES
    ('small_entanglement_study', 5, 30, TRUE),
    ('single_qubit_rotation_study', 2, 10, FALSE);

INSERT INTO quantum_experiments (
    owner_id, experiment_name, description, qubit_count,
    random_seed, maximum_operations
)
SELECT researcher_id, 'bell_pair_validation',
       'Prepare and validate a two-qubit Bell state.',
       2, 2026, 20
FROM researchers
WHERE username = 'atul_quantum';

INSERT INTO quantum_experiments (
    owner_id, experiment_name, description, qubit_count,
    random_seed, maximum_operations
)
SELECT researcher_id, 'three_qubit_ghz',
       'Prepare a three-qubit Greenberger-Horne-Zeilinger state.',
       3, 303, 30
FROM researchers
WHERE username = 'atul_quantum';

INSERT INTO circuit_operations (
    experiment_id, sequence_number, kind, target_qubit
)
SELECT experiment_id, 0, 'H', 0
FROM quantum_experiments
WHERE experiment_name = 'bell_pair_validation';

INSERT INTO circuit_operations (
    experiment_id, sequence_number, kind, target_qubit
)
SELECT experiment_id, 1, 'CX', 1
FROM quantum_experiments
WHERE experiment_name = 'bell_pair_validation';

INSERT INTO operation_controls (operation_id, control_qubit)
SELECT op.operation_id, 0
FROM circuit_operations op
JOIN quantum_experiments e USING (experiment_id)
WHERE e.experiment_name = 'bell_pair_validation'
  AND op.kind = 'CX';

INSERT INTO circuit_operations (
    experiment_id, sequence_number, kind, target_qubit
)
SELECT experiment_id, 0, 'H', 0
FROM quantum_experiments
WHERE experiment_name = 'three_qubit_ghz';

INSERT INTO circuit_operations (
    experiment_id, sequence_number, kind, target_qubit
)
SELECT experiment_id, 1, 'CX', 1
FROM quantum_experiments
WHERE experiment_name = 'three_qubit_ghz';

INSERT INTO operation_controls (operation_id, control_qubit)
SELECT op.operation_id, 0
FROM circuit_operations op
JOIN quantum_experiments e USING (experiment_id)
WHERE e.experiment_name = 'three_qubit_ghz'
  AND op.kind = 'CX';

INSERT INTO circuit_operations (
    experiment_id, sequence_number, kind, target_qubit
)
SELECT experiment_id, 2, 'CX', 2
FROM quantum_experiments
WHERE experiment_name = 'three_qubit_ghz';

INSERT INTO operation_controls (operation_id, control_qubit)
SELECT op.operation_id, 1
FROM circuit_operations op
JOIN quantum_experiments e USING (experiment_id)
WHERE e.experiment_name = 'three_qubit_ghz'
  AND op.sequence_number = 2;

-- Each validation call is a transactionally consistent state transition.
SELECT validate_experiment(
    e.experiment_id,
    p.policy_id,
    r.researcher_id
)
FROM quantum_experiments e
JOIN experiment_policies p
    ON p.policy_name = 'small_entanglement_study'
JOIN researchers r
    ON r.username = 'atul_quantum'
WHERE e.experiment_name IN (
    'bell_pair_validation',
    'three_qubit_ghz'
)
ORDER BY e.experiment_id;

INSERT INTO execution_runs (
    experiment_id, submitted_by, shots, backend_name,
    status, started_at
)
SELECT e.experiment_id, r.researcher_id, 1000,
       'statevector-local', 'running', CURRENT_TIMESTAMP
FROM quantum_experiments e
JOIN researchers r ON r.username = 'atul_quantum'
WHERE e.experiment_name = 'bell_pair_validation'
  AND e.status = 'validated';

INSERT INTO measurement_results (run_id, bitstring, occurrences)
SELECT run_id, '00', 503
FROM execution_runs
WHERE backend_name = 'statevector-local';

INSERT INTO measurement_results (run_id, bitstring, occurrences)
SELECT run_id, '11', 497
FROM execution_runs
WHERE backend_name = 'statevector-local';

UPDATE execution_runs
SET status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE backend_name = 'statevector-local';

-- Inventory query: identify circuits and their latest policy outcome.
SELECT *
FROM experiment_inventory
ORDER BY experiment_id;

-- Measurement query: compare observed frequencies with the expected
-- Bell-state support. A simulator should produce only 00 and 11 here.
SELECT
    result.run_id,
    result.bitstring,
    result.occurrences,
    run.shots,
    round(result.occurrences::numeric / run.shots, 4) AS observed_probability
FROM measurement_results result
JOIN execution_runs run USING (run_id)
ORDER BY result.run_id, result.bitstring;

-- A failed execution remains auditable and must carry an explicit error.
INSERT INTO execution_runs (
    experiment_id, submitted_by, shots, backend_name,
    status, error_message
)
SELECT e.experiment_id, r.researcher_id, 100,
       'unavailable-remote-backend', 'failed',
       'Backend was unavailable during job submission.'
FROM quantum_experiments e
JOIN researchers r ON r.username = 'atul_quantum'
WHERE e.experiment_name = 'bell_pair_validation'
  AND e.status = 'validated';

-- This query identifies incomplete runs without confusing queued jobs
-- with completed experiments.
SELECT run_id, experiment_id, status, error_message, created_at
FROM execution_runs
WHERE status IN ('queued', 'running', 'failed')
ORDER BY created_at DESC;

-- Demonstrate invalid gate protection in an isolated subtransaction.
-- The exception is caught so the complete learning script remains executable.
DO $$
DECLARE
    v_experiment_id BIGINT;
BEGIN
    SELECT experiment_id INTO v_experiment_id
    FROM quantum_experiments
    WHERE experiment_name = 'bell_pair_validation';

    BEGIN
        INSERT INTO circuit_operations (
            experiment_id, sequence_number, kind, target_qubit
        )
        VALUES (v_experiment_id, 99, 'X', 7);

        RAISE EXCEPTION 'Invalid target unexpectedly succeeded';
    EXCEPTION
        WHEN raise_exception THEN
            IF SQLERRM = 'Invalid target unexpectedly succeeded' THEN
                RAISE;
            END IF;
            RAISE NOTICE 'Expected validation rejection: %', SQLERRM;
    END;
END;
$$;

COMMIT;
