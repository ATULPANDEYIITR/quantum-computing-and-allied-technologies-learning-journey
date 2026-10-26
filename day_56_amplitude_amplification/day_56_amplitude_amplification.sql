DROP SCHEMA IF EXISTS quantum_search CASCADE;
CREATE SCHEMA quantum_search;

SET search_path TO quantum_search, public;

CREATE TYPE search_mode AS ENUM ('STANDARD', 'GENERALIZED');
CREATE TYPE experiment_state AS ENUM ('PLANNED', 'RUNNING', 'COMPLETED', 'FAILED');

CREATE TABLE search_problem (
    problem_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    n_qubits integer NOT NULL CHECK (n_qubits BETWEEN 1 AND 20),
    search_mode search_mode NOT NULL,
    target_probability numeric(12,10) NOT NULL
        CHECK (target_probability > 0 AND target_probability <= 1),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE marked_state (
    problem_id bigint NOT NULL
        REFERENCES search_problem(problem_id) ON DELETE CASCADE,
    state_value bigint NOT NULL CHECK (state_value >= 0),
    PRIMARY KEY (problem_id, state_value)
);

CREATE TABLE search_experiment (
    experiment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    problem_id bigint NOT NULL
        REFERENCES search_problem(problem_id) ON DELETE RESTRICT,
    state experiment_state NOT NULL DEFAULT 'PLANNED',
    requested_iterations integer NOT NULL CHECK (requested_iterations >= 0),
    started_at timestamptz,
    completed_at timestamptz,
    failure_reason text,
    CHECK (
        (state <> 'FAILED')
        OR failure_reason IS NOT NULL
    ),
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE TABLE amplification_step (
    experiment_id bigint NOT NULL
        REFERENCES search_experiment(experiment_id) ON DELETE CASCADE,
    iteration integer NOT NULL CHECK (iteration >= 0),
    good_amplitude double precision NOT NULL,
    bad_amplitude double precision NOT NULL,
    success_probability double precision NOT NULL
        CHECK (success_probability BETWEEN 0 AND 1),
    PRIMARY KEY (experiment_id, iteration)
);

CREATE TABLE oracle_evaluation (
    experiment_id bigint NOT NULL
        REFERENCES search_experiment(experiment_id) ON DELETE CASCADE,
    state_value bigint NOT NULL CHECK (state_value >= 0),
    is_marked boolean NOT NULL,
    measured_probability double precision NOT NULL
        CHECK (measured_probability >= 0 AND measured_probability <= 1),
    PRIMARY KEY (experiment_id, state_value)
);

CREATE TABLE search_policy (
    policy_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    policy_name text NOT NULL UNIQUE,
    minimum_success_probability numeric(12,10) NOT NULL
        CHECK (minimum_success_probability > 0
               AND minimum_success_probability <= 1),
    maximum_iterations integer NOT NULL CHECK (maximum_iterations >= 0),
    requires_exact_marked_count boolean NOT NULL DEFAULT false
);

CREATE TABLE repository_case (
    repository_case_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name text NOT NULL UNIQUE,
    branch_name text NOT NULL,
    required_approvals integer NOT NULL CHECK (required_approvals >= 0),
    require_passing_checks boolean NOT NULL DEFAULT true,
    require_resolved_conversations boolean NOT NULL DEFAULT true,
    direct_push_allowed boolean NOT NULL DEFAULT false,
    force_push_allowed boolean NOT NULL DEFAULT false
);

CREATE TABLE merge_case (
    merge_case_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_case_id bigint NOT NULL
        REFERENCES repository_case(repository_case_id) ON DELETE CASCADE,
    source_branch text NOT NULL,
    is_draft boolean NOT NULL DEFAULT false,
    has_conflict boolean NOT NULL DEFAULT false,
    synchronized_with_target boolean NOT NULL DEFAULT true,
    conversations_resolved boolean NOT NULL DEFAULT false,
    approvals integer NOT NULL DEFAULT 0 CHECK (approvals >= 0),
    status_checks_passing boolean NOT NULL DEFAULT false,
    merge_eligible boolean NOT NULL DEFAULT false
);

CREATE INDEX idx_marked_state_problem
    ON marked_state(problem_id);

CREATE INDEX idx_experiment_problem_state
    ON search_experiment(problem_id, state);

CREATE INDEX idx_amplification_probability
    ON amplification_step(experiment_id, success_probability DESC);

CREATE OR REPLACE FUNCTION validate_marked_state()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    dimension bigint;
BEGIN
    SELECT (1::bigint << n_qubits)
    INTO dimension
    FROM search_problem
    WHERE problem_id = NEW.problem_id;

    IF dimension IS NULL THEN
        RAISE EXCEPTION 'Search problem % does not exist',
            NEW.problem_id;
    END IF;

    IF NEW.state_value >= dimension THEN
        RAISE EXCEPTION
            'Marked state % is outside search dimension %',
            NEW.state_value,
            dimension;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_marked_state
BEFORE INSERT OR UPDATE ON marked_state
FOR EACH ROW
EXECUTE FUNCTION validate_marked_state();

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.state = 'COMPLETED'
       AND NEW.state <> 'COMPLETED' THEN
        RAISE EXCEPTION 'Completed experiments cannot be reopened';
    END IF;

    IF NEW.state = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at := now();
    END IF;

    IF NEW.state = 'COMPLETED' AND NEW.completed_at IS NULL THEN
        NEW.completed_at := now();
    END IF;

    IF NEW.state = 'FAILED' AND NEW.failure_reason IS NULL THEN
        RAISE EXCEPTION 'Failed experiments require failure_reason';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_transition
BEFORE UPDATE ON search_experiment
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();

CREATE OR REPLACE FUNCTION calculate_optimal_iterations(
    p_problem_id bigint
)
RETURNS integer
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    n integer;
    m bigint;
    theta double precision;
    estimate double precision;
    candidate integer;
    best integer := 0;
    best_probability double precision := -1;
    candidate_probability double precision;
BEGIN
    SELECT n_qubits
    INTO n
    FROM search_problem
    WHERE problem_id = p_problem_id;

    IF n IS NULL THEN
        RAISE EXCEPTION 'Unknown problem %', p_problem_id;
    END IF;

    SELECT count(*)
    INTO m
    FROM marked_state
    WHERE problem_id = p_problem_id;

    IF m = 0 THEN
        RAISE EXCEPTION 'Problem % has no marked states', p_problem_id;
    END IF;

    theta := asin(
        sqrt(
            m::double precision /
            (1::double precision * (1::bigint << n))
        )
    );

    estimate := pi() / (4.0 * theta) - 0.5;

    FOR candidate IN
        GREATEST(0, floor(estimate)::integer)
        .. GREATEST(0, floor(estimate)::integer + 1)
    LOOP
        candidate_probability :=
            power(
                sin((2.0 * candidate + 1.0) * theta),
                2.0
            );

        IF candidate_probability > best_probability THEN
            best_probability := candidate_probability;
            best := candidate;
        END IF;
    END LOOP;

    RETURN best;
END;
$$;

CREATE OR REPLACE VIEW problem_statistics AS
SELECT
    p.problem_id,
    p.name,
    p.n_qubits,
    p.search_mode,
    count(m.state_value) AS marked_count,
    round(
        count(m.state_value)::numeric /
        power(2::numeric, p.n_qubits),
        10
    ) AS initial_success_probability,
    calculate_optimal_iterations(p.problem_id) AS optimal_iterations
FROM search_problem p
LEFT JOIN marked_state m
    ON m.problem_id = p.problem_id
GROUP BY
    p.problem_id,
    p.name,
    p.n_qubits,
    p.search_mode;

CREATE OR REPLACE VIEW best_experiment_results AS
SELECT DISTINCT ON (experiment_id)
    experiment_id,
    iteration,
    success_probability
FROM amplification_step
ORDER BY experiment_id, success_probability DESC, iteration;

CREATE OR REPLACE VIEW merge_eligibility AS
SELECT
    m.merge_case_id,
    r.repository_name,
    r.branch_name AS protected_branch,
    m.source_branch,
    (
        NOT m.is_draft
        AND NOT m.has_conflict
        AND m.synchronized_with_target
        AND (
            NOT r.require_resolved_conversations
            OR m.conversations_resolved
        )
        AND m.approvals >= r.required_approvals
        AND (
            NOT r.require_passing_checks
            OR m.status_checks_passing
        )
    ) AS calculated_eligibility,
    m.merge_eligible AS recorded_eligibility
FROM merge_case m
JOIN repository_case r
    ON r.repository_case_id = m.repository_case_id;

INSERT INTO search_problem
    (name, n_qubits, search_mode, target_probability)
VALUES
    ('single-target-10-qubit-search', 10, 'STANDARD', 0.9900000000),
    ('four-target-10-qubit-search', 10, 'GENERALIZED', 0.9000000000),
    ('all-states-marked', 3, 'GENERALIZED', 0.9900000000);

INSERT INTO marked_state (problem_id, state_value)
SELECT problem_id, 777
FROM search_problem
WHERE name = 'single-target-10-qubit-search';

INSERT INTO marked_state (problem_id, state_value)
SELECT problem_id, value
FROM search_problem
CROSS JOIN LATERAL (
    VALUES (17::bigint), (211::bigint), (512::bigint), (777::bigint)
) AS values_table(value)
WHERE name = 'four-target-10-qubit-search';

INSERT INTO marked_state (problem_id, state_value)
SELECT problem_id, value
FROM search_problem
CROSS JOIN LATERAL generate_series(0, 7) AS values_table(value)
WHERE name = 'all-states-marked';

INSERT INTO search_policy
    (policy_name, minimum_success_probability, maximum_iterations)
VALUES
    ('standard-high-confidence', 0.9900000000, 10000),
    ('generalized-operational', 0.9000000000, 10000);

INSERT INTO search_experiment
    (problem_id, state, requested_iterations)
SELECT
    problem_id,
    'PLANNED',
    calculate_optimal_iterations(problem_id)
FROM search_problem
WHERE name IN (
    'single-target-10-qubit-search',
    'four-target-10-qubit-search',
    'all-states-marked'
);

-- The trajectory below uses the exact two-dimensional amplitude-amplification
-- relation P(k) = sin^2((2k+1)theta), where sin^2(theta)=M/N.
INSERT INTO amplification_step
    (experiment_id, iteration, good_amplitude, bad_amplitude, success_probability)
SELECT
    e.experiment_id,
    k,
    sin(
        (2.0 * k + 1.0) *
        asin(
            sqrt(
                ms.marked_count::double precision /
                (1::double precision * (1::bigint << p.n_qubits))
            )
        )
    ),
    cos(
        (2.0 * k + 1.0) *
        asin(
            sqrt(
                ms.marked_count::double precision /
                (1::double precision * (1::bigint << p.n_qubits))
            )
        )
    ),
    power(
        sin(
            (2.0 * k + 1.0) *
            asin(
                sqrt(
                    ms.marked_count::double precision /
                    (1::double precision * (1::bigint << p.n_qubits))
                )
            )
        ),
        2
    )
FROM search_experiment e
JOIN search_problem p
    ON p.problem_id = e.problem_id
JOIN LATERAL (
    SELECT count(*) AS marked_count
    FROM marked_state m
    WHERE m.problem_id = p.problem_id
) ms ON true
CROSS JOIN LATERAL generate_series(
    0,
    e.requested_iterations
) AS iteration(k);

INSERT INTO repository_case
    (repository_name, branch_name, required_approvals,
     require_passing_checks, require_resolved_conversations,
     direct_push_allowed, force_push_allowed)
VALUES
    ('quantum-search-engine', 'main', 2, true, true, false, false);

INSERT INTO merge_case
    (repository_case_id, source_branch, is_draft, has_conflict,
     synchronized_with_target, conversations_resolved,
     approvals, status_checks_passing, merge_eligible)
SELECT
    repository_case_id,
    'feature/generalized-amplification',
    false,
    false,
    true,
    true,
    2,
    true,
    true
FROM repository_case
WHERE repository_name = 'quantum-search-engine';

INSERT INTO merge_case
    (repository_case_id, source_branch, is_draft, has_conflict,
     synchronized_with_target, conversations_resolved,
     approvals, status_checks_passing, merge_eligible)
SELECT
    repository_case_id,
    'feature/stale-oracle-model',
    false,
    false,
    true,
    false,
    1,
    true,
    false
FROM repository_case
WHERE repository_name = 'quantum-search-engine';

-- Retrieval: distinguish ordinary and generalized search.
SELECT *
FROM problem_statistics
ORDER BY problem_id;

-- Evaluation: identify the best amplification point for every experiment.
SELECT
    e.experiment_id,
    p.name,
    b.iteration,
    b.success_probability
FROM search_experiment e
JOIN search_problem p
    ON p.problem_id = e.problem_id
JOIN best_experiment_results b
    ON b.experiment_id = e.experiment_id
ORDER BY e.experiment_id;

-- Aggregation: compare the asymptotic scaling proxy sqrt(N/M).
SELECT
    p.name,
    p.n_qubits,
    count(m.state_value) AS marked_count,
    sqrt(
        (1::double precision * (1::bigint << p.n_qubits)) /
        count(m.state_value)
    ) AS sqrt_n_over_m
FROM search_problem p
JOIN marked_state m
    ON m.problem_id = p.problem_id
GROUP BY p.problem_id, p.name, p.n_qubits
ORDER BY p.n_qubits, marked_count;

-- Validation: find experiments that violate their configured probability policy.
SELECT
    e.experiment_id,
    p.name,
    max(a.success_probability) AS best_probability,
    sp.minimum_success_probability
FROM search_experiment e
JOIN search_problem p
    ON p.problem_id = e.problem_id
JOIN amplification_step a
    ON a.experiment_id = e.experiment_id
JOIN search_policy sp
    ON (
        p.search_mode = 'STANDARD'
        AND sp.policy_name = 'standard-high-confidence'
    )
    OR (
        p.search_mode = 'GENERALIZED'
        AND sp.policy_name = 'generalized-operational'
    )
GROUP BY
    e.experiment_id,
    p.name,
    sp.minimum_success_probability
HAVING max(a.success_probability) < sp.minimum_success_probability;

-- Workflow state report.
SELECT
    experiment_id,
    state,
    requested_iterations,
    started_at,
    completed_at,
    failure_reason
FROM search_experiment
ORDER BY experiment_id;

-- Repository governance: distinguish recorded state from calculated policy.
SELECT
    repository_name,
    protected_branch,
    source_branch,
    calculated_eligibility,
    recorded_eligibility
FROM merge_eligibility
ORDER BY merge_case_id;

-- Transactional example: a run is moved from planned to running,
-- measurements are persisted, then the experiment is completed atomically.
BEGIN;

UPDATE search_experiment
SET state = 'RUNNING'
WHERE experiment_id = (
    SELECT min(experiment_id)
    FROM search_experiment
    WHERE state = 'PLANNED'
);

UPDATE search_experiment
SET state = 'COMPLETED'
WHERE experiment_id = (
    SELECT min(experiment_id)
    FROM search_experiment
    WHERE state = 'RUNNING'
);

COMMIT;

-- Failure handling example. This deliberately rolls back so the sample
-- dataset remains valid for repeated execution.
BEGIN;

UPDATE search_experiment
SET state = 'FAILED',
    failure_reason = 'Synthetic oracle validation failure'
WHERE experiment_id = (
    SELECT max(experiment_id)
    FROM search_experiment
);

ROLLBACK;
