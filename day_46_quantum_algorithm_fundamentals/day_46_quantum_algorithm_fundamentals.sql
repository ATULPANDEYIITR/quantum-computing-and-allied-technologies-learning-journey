-- PostgreSQL 14+
-- Quantum algorithm fundamentals: experiment design, oracle contracts,
-- circuit execution records, resource budgets, and result verification.

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TABLE IF NOT EXISTS algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_name TEXT NOT NULL UNIQUE,
    problem_class TEXT NOT NULL CHECK (
        problem_class IN (
            'PROMISE_PROBLEM',
            'HIDDEN_BIT_STRING',
            'UNSTRUCTURED_SEARCH'
        )
    ),
    oracle_query_model TEXT NOT NULL,
    ideal_query_complexity TEXT NOT NULL,
    classical_comparison TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    algorithm_id BIGINT NOT NULL REFERENCES algorithms(algorithm_id),
    experiment_name TEXT NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (qubit_count BETWEEN 1 AND 30),
    search_space_size BIGINT GENERATED ALWAYS AS (
        power(2::numeric, qubit_count)::BIGINT
    ) STORED,
    marked_state_count BIGINT,
    requested_shots INTEGER NOT NULL CHECK (requested_shots BETWEEN 1 AND 10000000),
    oracle_validated BOOLEAN NOT NULL DEFAULT FALSE,
    hardware_backend TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'CREATED' CHECK (
        status IN ('CREATED', 'VALIDATED', 'RUNNING', 'COMPLETED', 'FAILED')
    ),
    CHECK (
        marked_state_count IS NULL OR
        marked_state_count BETWEEN 1 AND search_space_size
    ),
    UNIQUE (experiment_name)
);

CREATE TABLE IF NOT EXISTS circuit_stages (
    stage_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    stage_position INTEGER NOT NULL CHECK (stage_position >= 0),
    gate_name TEXT NOT NULL CHECK (
        gate_name IN (
            'INITIALIZATION',
            'HADAMARD_LAYER',
            'ORACLE',
            'DIFFUSION',
            'ENTANGLEMENT',
            'MEASUREMENT'
        )
    ),
    target_qubits INTEGER[] NOT NULL DEFAULT '{}',
    estimated_gate_count BIGINT NOT NULL CHECK (estimated_gate_count >= 0),
    notes TEXT NOT NULL,
    UNIQUE (experiment_id, stage_position)
);

CREATE TABLE IF NOT EXISTS oracle_contracts (
    oracle_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    oracle_kind TEXT NOT NULL CHECK (
        oracle_kind IN ('BOOLEAN', 'PHASE', 'BIT_STRING_PARITY')
    ),
    reversible BOOLEAN NOT NULL,
    deterministic BOOLEAN NOT NULL,
    verification_method TEXT NOT NULL,
    verified_at TIMESTAMPTZ,
    CHECK (
        verified_at IS NULL OR verified_at <= CURRENT_TIMESTAMP
    )
);

CREATE TABLE IF NOT EXISTS experiment_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    measured_state BIGINT NOT NULL CHECK (measured_state >= 0),
    observed_shots INTEGER NOT NULL CHECK (observed_shots > 0),
    target_hits INTEGER NOT NULL CHECK (
        target_hits >= 0 AND target_hits <= observed_shots
    ),
    target_probability NUMERIC(12, 10) GENERATED ALWAYS AS (
        target_hits::NUMERIC / observed_shots
    ) STORED,
    oracle_queries INTEGER NOT NULL CHECK (oracle_queries >= 0),
    execution_duration_ms NUMERIC(14, 3) NOT NULL CHECK (
        execution_duration_ms >= 0
    ),
    verification_status TEXT NOT NULL CHECK (
        verification_status IN ('PENDING', 'PASSED', 'FAILED')
    ),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (measured_state < 1073741824)
);

CREATE TABLE IF NOT EXISTS resource_budgets (
    budget_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    maximum_qubits INTEGER NOT NULL CHECK (maximum_qubits > 0),
    maximum_shots INTEGER NOT NULL CHECK (maximum_shots > 0),
    maximum_gate_count BIGINT NOT NULL CHECK (maximum_gate_count > 0),
    approved_by TEXT NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_results_experiment_recorded
    ON experiment_results(experiment_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_circuit_stages_gate
    ON circuit_stages(gate_name, experiment_id);

INSERT INTO algorithms (
    algorithm_name, problem_class, oracle_query_model,
    ideal_query_complexity, classical_comparison, description
)
VALUES
(
    'Deutsch',
    'PROMISE_PROBLEM',
    'One Boolean oracle query',
    'O(1) queries',
    'Up to two evaluations for a deterministic classical decision',
    'Distinguishes constant from balanced one-bit Boolean functions.'
),
(
    'Bernstein-Vazirani',
    'HIDDEN_BIT_STRING',
    'Parity oracle over an unknown bit string',
    'One quantum oracle query',
    'Up to n classical queries for deterministic recovery',
    'Recovers a hidden bit string under the parity-oracle promise.'
),
(
    'Grover',
    'UNSTRUCTURED_SEARCH',
    'Phase oracle marking satisfying candidates',
    'O(sqrt(N/M)) queries',
    'O(N/M) expected queries for random-order classical search',
    'Amplifies marked-state amplitudes in an unstructured search space.'
)
ON CONFLICT (algorithm_name) DO NOTHING;

INSERT INTO experiments (
    algorithm_id, experiment_name, qubit_count, marked_state_count,
    requested_shots, oracle_validated, hardware_backend, status
)
SELECT algorithm_id, 'Build failure diagnosis', 8, 1, 2000,
       TRUE, 'ideal-statevector', 'VALIDATED'
FROM algorithms
WHERE algorithm_name = 'Grover'
ON CONFLICT (experiment_name) DO NOTHING;

INSERT INTO oracle_contracts (
    experiment_id, oracle_kind, reversible, deterministic,
    verification_method, verified_at
)
SELECT experiment_id, 'PHASE', TRUE, TRUE,
       'Exhaustive predicate comparison over all 256 basis states',
       CURRENT_TIMESTAMP
FROM experiments
WHERE experiment_name = 'Build failure diagnosis'
ON CONFLICT (experiment_id) DO NOTHING;

INSERT INTO circuit_stages (
    experiment_id, stage_position, gate_name, target_qubits,
    estimated_gate_count, notes
)
SELECT experiment_id, stage.stage_position, stage.gate_name,
       stage.target_qubits, stage.estimated_gate_count, stage.notes
FROM experiments
CROSS JOIN (
    VALUES
        (0, 'INITIALIZATION', ARRAY[]::INTEGER[], 8::BIGINT,
         'Prepare the all-zero register.'),
        (1, 'HADAMARD_LAYER', ARRAY[0,1,2,3,4,5,6,7], 8::BIGINT,
         'Create a uniform superposition over 256 candidates.'),
        (2, 'ORACLE', ARRAY[0,1,2,3,4,5,6,7], 1::BIGINT,
         'Reverse phase for the declared faulty build.'),
        (3, 'DIFFUSION', ARRAY[0,1,2,3,4,5,6,7], 8::BIGINT,
         'Reflect amplitudes around their mean.'),
        (4, 'MEASUREMENT', ARRAY[0,1,2,3,4,5,6,7], 8::BIGINT,
         'Convert amplitudes into a classical outcome.')
) AS stage(stage_position, gate_name, target_qubits, estimated_gate_count, notes)
WHERE experiments.experiment_name = 'Build failure diagnosis'
ON CONFLICT (experiment_id, stage_position) DO NOTHING;

INSERT INTO resource_budgets (
    experiment_id, maximum_qubits, maximum_shots, maximum_gate_count, approved_by
)
SELECT experiment_id, 8, 5000, 100000, 'quantum-lab-reviewer'
FROM experiments
WHERE experiment_name = 'Build failure diagnosis'
ON CONFLICT (experiment_id) DO NOTHING;

-- The trigger prevents accidental execution-state changes that skip oracle
-- validation or attempt to restart a terminal experiment.
CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'FAILED') AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'Terminal experiment status cannot be changed';
    END IF;

    IF NEW.status = 'VALIDATED' AND NOT NEW.oracle_validated THEN
        RAISE EXCEPTION 'Oracle validation is required before VALIDATED status';
    END IF;

    IF NEW.status = 'RUNNING' AND OLD.status NOT IN ('VALIDATED', 'RUNNING') THEN
        RAISE EXCEPTION 'Experiment must be validated before execution';
    END IF;

    IF NEW.status = 'COMPLETED' AND OLD.status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Only a running experiment can be completed';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_experiment_transition ON experiments;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- Enforce that measurement indices fit the experiment's Hilbert space and
-- that observed shots do not exceed the configured budget.
CREATE OR REPLACE FUNCTION validate_experiment_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_row experiments%ROWTYPE;
    budget_row resource_budgets%ROWTYPE;
BEGIN
    SELECT * INTO STRICT experiment_row
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF NEW.measured_state >= experiment_row.search_space_size THEN
        RAISE EXCEPTION 'Measured state exceeds search-space dimension';
    END IF;

    SELECT * INTO STRICT budget_row
    FROM resource_budgets
    WHERE experiment_id = NEW.experiment_id;

    IF NEW.observed_shots > budget_row.maximum_shots THEN
        RAISE EXCEPTION 'Observed shots exceed approved resource budget';
    END IF;

    IF experiment_row.status NOT IN ('RUNNING', 'COMPLETED') THEN
        RAISE EXCEPTION 'Results require a running or completed experiment';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_experiment_result ON experiment_results;

CREATE TRIGGER trg_validate_experiment_result
BEFORE INSERT OR UPDATE ON experiment_results
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_result();

-- This view estimates the observed probability of measuring a marked state.
-- It does not infer correctness merely from a high measured probability.
CREATE OR REPLACE VIEW experiment_resource_report AS
SELECT
    e.experiment_name,
    a.algorithm_name,
    e.qubit_count,
    e.search_space_size,
    e.marked_state_count,
    e.requested_shots,
    e.status,
    COALESCE(SUM(s.estimated_gate_count), 0) AS estimated_gate_count,
    MAX(r.oracle_queries) AS recorded_oracle_queries,
    MAX(r.target_probability) AS observed_target_probability,
    BOOL_AND(r.verification_status = 'PASSED')
        FILTER (WHERE r.result_id IS NOT NULL) AS all_results_passed
FROM experiments AS e
JOIN algorithms AS a ON a.algorithm_id = e.algorithm_id
LEFT JOIN circuit_stages AS s ON s.experiment_id = e.experiment_id
LEFT JOIN experiment_results AS r ON r.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id, e.experiment_name, a.algorithm_name,
    e.qubit_count, e.search_space_size, e.marked_state_count,
    e.requested_shots, e.status;

-- Validate the oracle record and resource budget before changing state.
UPDATE experiments AS e
SET status = 'RUNNING'
FROM oracle_contracts AS o
JOIN resource_budgets AS b ON b.experiment_id = o.experiment_id
WHERE e.experiment_id = o.experiment_id
  AND e.experiment_name = 'Build failure diagnosis'
  AND e.status = 'VALIDATED'
  AND e.oracle_validated
  AND o.reversible
  AND o.deterministic
  AND o.verified_at IS NOT NULL
  AND e.qubit_count <= b.maximum_qubits
  AND e.requested_shots <= b.maximum_shots;

INSERT INTO experiment_results (
    experiment_id, measured_state, observed_shots, target_hits,
    oracle_queries, execution_duration_ms, verification_status
)
SELECT
    experiment_id, 173, 2000, 1750, 3, 12.500, 'PASSED'
FROM experiments
WHERE experiment_name = 'Build failure diagnosis'
  AND status = 'RUNNING'
ON CONFLICT DO NOTHING;

UPDATE experiments
SET status = 'COMPLETED'
WHERE experiment_name = 'Build failure diagnosis'
  AND status = 'RUNNING'
  AND EXISTS (
      SELECT 1
      FROM experiment_results AS r
      WHERE r.experiment_id = experiments.experiment_id
        AND r.verification_status = 'PASSED'
  );

-- The query compares measured outcomes with the declared target set.
SELECT
    e.experiment_name,
    a.algorithm_name,
    r.measured_state,
    r.observed_shots,
    r.target_hits,
    r.target_probability,
    r.oracle_queries,
    r.verification_status,
    e.status
FROM experiment_results AS r
JOIN experiments AS e USING (experiment_id)
JOIN algorithms AS a USING (algorithm_id)
ORDER BY r.recorded_at DESC;

SELECT *
FROM experiment_resource_report
ORDER BY experiment_name;

-- A failed constraint or trigger aborts the current statement. The transaction
-- keeps the schema, seed records, and demonstration workflow atomic.
COMMIT;
