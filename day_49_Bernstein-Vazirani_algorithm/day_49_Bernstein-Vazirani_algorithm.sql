-- Bernstein-Vazirani Algorithm
-- PostgreSQL-compatible relational model for hidden-string experiments.
--
-- The schema separates:
--   repositories and protected branches
--   quantum experiments and hidden-string metadata
--   oracle queries and observed responses
--   classical baselines
--   circuit gates
--   verification and policy decisions
--
-- This database models the experiment lifecycle rather than attempting to
-- represent a quantum computer's physical hardware.

DROP SCHEMA IF EXISTS bernstein_vazirani CASCADE;
CREATE SCHEMA bernstein_vazirani;

SET search_path TO bernstein_vazirani;

CREATE TYPE experiment_state AS ENUM (
    'created',
    'validated',
    'executed',
    'verified',
    'failed'
);

CREATE TYPE decision_status AS ENUM (
    'pass',
    'fail'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE protected_branches (
    branch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_name TEXT NOT NULL,
    requires_verified_experiment BOOLEAN NOT NULL DEFAULT TRUE,
    requires_single_quantum_oracle_query BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (repository_id, branch_name)
);

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE RESTRICT,
    branch_id BIGINT NOT NULL
        REFERENCES protected_branches(branch_id)
        ON DELETE RESTRICT,
    experiment_key TEXT NOT NULL UNIQUE,
    hidden_width INTEGER NOT NULL
        CHECK (hidden_width > 0),
    hidden_string TEXT NOT NULL,
    state experiment_state NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    CHECK (length(hidden_string) = hidden_width),
    CHECK (hidden_string ~ '^[01]+$'),
    CHECK (
        (state IN ('executed', 'verified') AND executed_at IS NOT NULL)
        OR state IN ('created', 'validated', 'failed')
    ),
    CHECK (
        state <> 'verified' OR verified_at IS NOT NULL
    )
);

CREATE TABLE oracle_queries (
    query_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    query_number INTEGER NOT NULL
        CHECK (query_number > 0),
    input_bits TEXT NOT NULL,
    output_bit INTEGER NOT NULL
        CHECK (output_bit IN (0, 1)),
    query_kind TEXT NOT NULL
        CHECK (query_kind IN ('classical', 'quantum')),
    queried_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (experiment_id, query_number, query_kind),
    CHECK (input_bits ~ '^[01]+$')
);

CREATE TABLE classical_baselines (
    baseline_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    recovered_string TEXT NOT NULL,
    oracle_queries INTEGER NOT NULL
        CHECK (oracle_queries > 0),
    verification decision_status NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    gate_order INTEGER NOT NULL
        CHECK (gate_order > 0),
    gate_type TEXT NOT NULL
        CHECK (gate_type IN ('H', 'CNOT')),
    control_qubit INTEGER,
    target_qubit INTEGER,
    CHECK (
        gate_type = 'H'
        AND control_qubit IS NULL
        AND target_qubit >= 0
        OR
        gate_type = 'CNOT'
        AND control_qubit >= 0
        AND target_qubit >= 0
        AND control_qubit <> target_qubit
    ),
    UNIQUE (experiment_id, gate_order)
);

CREATE TABLE experiment_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    recovered_string TEXT NOT NULL,
    quantum_oracle_queries INTEGER NOT NULL
        CHECK (quantum_oracle_queries >= 0),
    verification decision_status NOT NULL,
    policy_decision decision_status NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (recovered_string ~ '^[01]+$')
);

CREATE INDEX idx_experiments_repository_state
    ON experiments(repository_id, state);

CREATE INDEX idx_oracle_queries_experiment_kind
    ON oracle_queries(experiment_id, query_kind);

CREATE INDEX idx_results_policy_decision
    ON experiment_results(policy_decision);

CREATE INDEX idx_circuit_gates_experiment_order
    ON circuit_gates(experiment_id, gate_order);

INSERT INTO repositories (repository_name, owner_name)
VALUES
    ('quantum-learning-lab', 'research-platform'),
    ('quantum-governance-demo', 'platform-engineering');

INSERT INTO protected_branches (
    repository_id,
    branch_name,
    requires_verified_experiment,
    requires_single_quantum_oracle_query
)
SELECT
    repository_id,
    'main',
    TRUE,
    TRUE
FROM repositories;

INSERT INTO experiments (
    repository_id,
    branch_id,
    experiment_key,
    hidden_width,
    hidden_string,
    state,
    executed_at,
    verified_at
)
SELECT
    r.repository_id,
    b.branch_id,
    'BV-2026-001',
    6,
    '101101',
    'verified',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM repositories r
JOIN protected_branches b
    ON b.repository_id = r.repository_id
WHERE r.repository_name = 'quantum-learning-lab'
  AND b.branch_name = 'main';

INSERT INTO experiments (
    repository_id,
    branch_id,
    experiment_key,
    hidden_width,
    hidden_string,
    state
)
SELECT
    r.repository_id,
    b.branch_id,
    'BV-2026-002',
    5,
    '11010',
    'validated'
FROM repositories r
JOIN protected_branches b
    ON b.repository_id = r.repository_id
WHERE r.repository_name = 'quantum-governance-demo'
  AND b.branch_name = 'main';

INSERT INTO oracle_queries (
    experiment_id,
    query_number,
    input_bits,
    output_bit,
    query_kind
)
SELECT
    e.experiment_id,
    1,
    '000001',
    1,
    'quantum'
FROM experiments e
WHERE e.experiment_key = 'BV-2026-001';

INSERT INTO classical_baselines (
    experiment_id,
    recovered_string,
    oracle_queries,
    verification
)
SELECT
    experiment_id,
    hidden_string,
    hidden_width,
    'pass'
FROM experiments
WHERE experiment_key = 'BV-2026-001';

INSERT INTO circuit_gates (
    experiment_id,
    gate_order,
    gate_type,
    control_qubit,
    target_qubit
)
SELECT
    e.experiment_id,
    ROW_NUMBER() OVER (ORDER BY q.position) * 10,
    'H',
    NULL,
    q.position
FROM experiments e
CROSS JOIN LATERAL generate_series(
    0,
    e.hidden_width
) AS q(position)
WHERE e.experiment_key = 'BV-2026-001';

INSERT INTO circuit_gates (
    experiment_id,
    gate_order,
    gate_type,
    control_qubit,
    target_qubit
)
SELECT
    e.experiment_id,
    100 + ROW_NUMBER() OVER (ORDER BY q.position),
    'CNOT',
    q.position,
    e.hidden_width
FROM experiments e
CROSS JOIN LATERAL generate_series(
    0,
    e.hidden_width - 1
) AS q(position)
WHERE e.experiment_key = 'BV-2026-001'
  AND SUBSTRING(e.hidden_string FROM q.position + 1 FOR 1) = '1';

INSERT INTO experiment_results (
    experiment_id,
    recovered_string,
    quantum_oracle_queries,
    verification,
    policy_decision
)
SELECT
    experiment_id,
    hidden_string,
    1,
    'pass',
    CASE
        WHEN state = 'verified'
         AND hidden_width > 0
        THEN 'pass'::decision_status
        ELSE 'fail'::decision_status
    END
FROM experiments
WHERE experiment_key = 'BV-2026-001';

-- The following view exposes the database-level interpretation of
-- Bernstein-Vazirani merge/acceptance conditions:
-- the recovered string must match the stored hidden configuration,
-- the experiment must be verified, and the quantum oracle must be used once.

CREATE VIEW experiment_policy_report AS
SELECT
    e.experiment_key,
    r.repository_name,
    b.branch_name,
    e.hidden_width,
    e.hidden_string,
    er.recovered_string,
    er.quantum_oracle_queries,
    e.state,
    b.requires_verified_experiment,
    b.requires_single_quantum_oracle_query,
    CASE
        WHEN er.recovered_string = e.hidden_string
         AND (
             NOT b.requires_verified_experiment
             OR e.state = 'verified'
         )
         AND (
             NOT b.requires_single_quantum_oracle_query
             OR er.quantum_oracle_queries = 1
         )
        THEN 'pass'
        ELSE 'fail'
    END AS effective_decision
FROM experiments e
JOIN repositories r
    ON r.repository_id = e.repository_id
JOIN protected_branches b
    ON b.branch_id = e.branch_id
LEFT JOIN experiment_results er
    ON er.experiment_id = e.experiment_id;

-- Inspect verified experiments and their query complexity.
SELECT
    experiment_key,
    hidden_width,
    hidden_string,
    recovered_string,
    quantum_oracle_queries,
    effective_decision
FROM experiment_policy_report
ORDER BY experiment_key;

-- Compare the classical unit-vector baseline against the quantum oracle.
SELECT
    e.experiment_key,
    e.hidden_width,
    cb.oracle_queries AS classical_queries,
    er.quantum_oracle_queries AS quantum_queries,
    cb.oracle_queries - er.quantum_oracle_queries
        AS query_reduction
FROM experiments e
JOIN classical_baselines cb
    ON cb.experiment_id = e.experiment_id
JOIN experiment_results er
    ON er.experiment_id = e.experiment_id;

-- Identify hidden-string positions that require CNOT controls.
SELECT
    e.experiment_key,
    g.control_qubit,
    g.target_qubit
FROM experiments e
JOIN circuit_gates g
    ON g.experiment_id = e.experiment_id
WHERE g.gate_type = 'CNOT'
ORDER BY e.experiment_key, g.control_qubit;

-- Validate that the recorded quantum query count satisfies the
-- protected-branch policy.
SELECT
    experiment_key,
    branch_name,
    quantum_oracle_queries,
    CASE
        WHEN requires_single_quantum_oracle_query
         AND quantum_oracle_queries <> 1
        THEN 'policy failure'
        ELSE 'policy satisfied'
    END AS query_policy_status
FROM experiment_policy_report;

-- Demonstrate a transaction around experiment verification.
BEGIN;

UPDATE experiments
SET state = 'verified',
    verified_at = CURRENT_TIMESTAMP
WHERE experiment_key = 'BV-2026-001'
  AND state = 'executed';

COMMIT;

-- A malformed hidden string is rejected by the CHECK constraint.
-- The statement is intentionally kept commented so that this complete
-- demonstration script remains executable without failure.
--
-- INSERT INTO experiments (
--     repository_id,
--     branch_id,
--     experiment_key,
--     hidden_width,
--     hidden_string
-- )
-- SELECT repository_id, branch_id, 'BV-INVALID', 4, '1021'
-- FROM experiments
-- WHERE experiment_key = 'BV-2026-001'
-- LIMIT 1;
