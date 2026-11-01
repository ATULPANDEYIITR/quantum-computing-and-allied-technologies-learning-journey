DROP SCHEMA IF EXISTS superconducting_qubits CASCADE;

CREATE SCHEMA superconducting_qubits;

SET search_path TO superconducting_qubits, public;

CREATE TYPE repository_component AS ENUM (
    'JUNCTION',
    'TRANSMON',
    'RF_SQUID',
    'CONTROL_LINE',
    'READOUT'
);

CREATE TYPE circuit_state AS ENUM (
    'DESIGNED',
    'FABRICATED',
    'COOLED',
    'CHARACTERIZED',
    'CALIBRATED',
    'FAILED',
    'RETIRED'
);

CREATE TYPE measurement_basis AS ENUM (
    'Z',
    'X',
    'Y'
);

CREATE TYPE check_state AS ENUM (
    'PENDING',
    'PASS',
    'FAIL',
    'NOT_RUN'
);

CREATE TYPE review_state AS ENUM (
    'COMMENTED',
    'APPROVED',
    'CHANGES_REQUESTED',
    'DISMISSED'
);

CREATE TYPE merge_state AS ENUM (
    'OPEN',
    'ELIGIBLE',
    'BLOCKED',
    'MERGED',
    'CLOSED'
);

CREATE TABLE repositories (
    repository_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(name)) >= 2),
    CHECK (length(trim(owner)) >= 2)
);

CREATE TABLE branches (
    branch_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    protected BOOLEAN NOT NULL DEFAULT FALSE,
    default_branch BOOLEAN NOT NULL DEFAULT FALSE,
    head_commit_sha CHAR(40),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, name),
    CHECK (name <> '')
);

CREATE UNIQUE INDEX one_default_branch_per_repository
ON branches(repository_id)
WHERE default_branch;

CREATE TABLE commits (
    commit_sha CHAR(40) PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    branch_id BIGINT
        REFERENCES branches(branch_id)
        ON DELETE SET NULL,
    parent_sha CHAR(40)
        REFERENCES commits(commit_sha)
        ON DELETE SET NULL,
    author TEXT NOT NULL,
    message TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    CHECK (commit_sha ~ '^[0-9a-f]{40}$'),
    CHECK (length(trim(author)) > 0),
    CHECK (length(trim(message)) > 0)
);

CREATE TABLE contributors (
    contributor_id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    role_name TEXT NOT NULL,
    CHECK (position('@' IN email) > 1)
);

CREATE TABLE pull_requests (
    pull_request_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    source_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    target_branch_id BIGINT NOT NULL
        REFERENCES branches(branch_id)
        ON DELETE RESTRICT,
    author_id BIGINT NOT NULL
        REFERENCES contributors(contributor_id)
        ON DELETE RESTRICT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    draft BOOLEAN NOT NULL DEFAULT TRUE,
    state merge_state NOT NULL DEFAULT 'OPEN',
    head_commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    base_commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    merged_at TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) >= 5)
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha)
        ON DELETE RESTRICT,
    position_no INTEGER NOT NULL,
    PRIMARY KEY (pull_request_id, commit_sha),
    UNIQUE (pull_request_id, position_no),
    CHECK (position_no > 0)
);

CREATE TABLE reviewers (
    reviewer_id BIGSERIAL PRIMARY KEY,
    contributor_id BIGINT NOT NULL UNIQUE
        REFERENCES contributors(contributor_id)
        ON DELETE CASCADE,
    security_team BOOLEAN NOT NULL DEFAULT FALSE,
    senior_engineer BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE reviews (
    review_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    reviewer_id BIGINT NOT NULL
        REFERENCES reviewers(reviewer_id)
        ON DELETE RESTRICT,
    state review_state NOT NULL,
    body TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    dismissed_at TIMESTAMPTZ,
    CHECK (length(trim(body)) > 0),
    CHECK (
        (state = 'DISMISSED' AND dismissed_at IS NOT NULL)
        OR
        (state <> 'DISMISSED')
    )
);

CREATE TABLE review_comments (
    comment_id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL
        REFERENCES reviews(review_id)
        ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    body TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ,
    CHECK (line_number > 0),
    CHECK (length(trim(file_path)) > 0),
    CHECK (length(trim(body)) > 0),
    CHECK (
        (resolved = TRUE AND resolved_at IS NOT NULL)
        OR
        resolved = FALSE
    )
);

CREATE TABLE status_checks (
    status_check_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    check_name TEXT NOT NULL,
    state check_state NOT NULL,
    commit_sha CHAR(40) NOT NULL
        REFERENCES commits(commit_sha),
    completed_at TIMESTAMPTZ,
    details TEXT NOT NULL,
    UNIQUE (pull_request_id, check_name, commit_sha),
    CHECK (length(trim(check_name)) > 0)
);

CREATE TABLE branch_protection_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    branch_id BIGINT NOT NULL UNIQUE
        REFERENCES branches(branch_id)
        ON DELETE CASCADE,
    required_reviews INTEGER NOT NULL DEFAULT 1,
    dismiss_stale_reviews BOOLEAN NOT NULL DEFAULT TRUE,
    require_status_checks BOOLEAN NOT NULL DEFAULT TRUE,
    allow_direct_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_force_push BOOLEAN NOT NULL DEFAULT FALSE,
    allow_branch_deletion BOOLEAN NOT NULL DEFAULT FALSE,
    require_conversation_resolution BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history BOOLEAN NOT NULL DEFAULT FALSE,
    allow_administrator_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (required_reviews BETWEEN 0 AND 20)
);

CREATE TABLE approval_requirements (
    requirement_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT NOT NULL
        REFERENCES branch_protection_policies(policy_id)
        ON DELETE CASCADE,
    reviewer_role TEXT NOT NULL,
    required_count INTEGER NOT NULL,
    UNIQUE (policy_id, reviewer_role),
    CHECK (required_count > 0),
    CHECK (length(trim(reviewer_role)) > 0)
);

CREATE TABLE circuits (
    circuit_id BIGSERIAL PRIMARY KEY,
    repository_id BIGINT NOT NULL
        REFERENCES repositories(repository_id)
        ON DELETE CASCADE,
    name TEXT NOT NULL,
    component_type repository_component NOT NULL,
    state circuit_state NOT NULL DEFAULT 'DESIGNED',
    critical_current_a DOUBLE PRECISION,
    capacitance_f DOUBLE PRECISION,
    normal_resistance_ohm DOUBLE PRECISION,
    loop_inductance_h DOUBLE PRECISION,
    charging_energy_j DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository_id, name),
    CHECK (
        critical_current_a IS NULL
        OR critical_current_a > 0
    ),
    CHECK (
        capacitance_f IS NULL
        OR capacitance_f > 0
    ),
    CHECK (
        normal_resistance_ohm IS NULL
        OR normal_resistance_ohm > 0
    ),
    CHECK (
        loop_inductance_h IS NULL
        OR loop_inductance_h > 0
    ),
    CHECK (
        charging_energy_j IS NULL
        OR charging_energy_j > 0
    )
);

CREATE TABLE qubit_measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    basis measurement_basis NOT NULL,
    shots INTEGER NOT NULL,
    zero_count INTEGER NOT NULL,
    one_count INTEGER NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (shots > 0),
    CHECK (zero_count >= 0),
    CHECK (one_count >= 0),
    CHECK (zero_count + one_count = shots)
);

CREATE TABLE merge_eligibility (
    eligibility_id BIGSERIAL PRIMARY KEY,
    pull_request_id BIGINT NOT NULL UNIQUE
        REFERENCES pull_requests(pull_request_id)
        ON DELETE CASCADE,
    eligible BOOLEAN NOT NULL,
    approval_count INTEGER NOT NULL,
    passing_check_count INTEGER NOT NULL,
    unresolved_comment_count INTEGER NOT NULL,
    reason TEXT NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (approval_count >= 0),
    CHECK (passing_check_count >= 0),
    CHECK (unresolved_comment_count >= 0),
    CHECK (length(trim(reason)) > 0)
);

CREATE INDEX idx_branches_repository
ON branches(repository_id);

CREATE INDEX idx_pr_target_state
ON pull_requests(target_branch_id, state);

CREATE INDEX idx_reviews_pr_state
ON reviews(pull_request_id, state);

CREATE INDEX idx_status_checks_pr_state
ON status_checks(pull_request_id, state);

CREATE INDEX idx_circuits_repository_state
ON circuits(repository_id, state);

INSERT INTO repositories (
    name,
    owner,
    description
)
VALUES (
    'superconducting-qubit-control',
    'quantum-lab',
    'Josephson-junction and transmon circuit research repository'
);

INSERT INTO branches (
    repository_id,
    name,
    protected,
    default_branch
)
VALUES
(
    1,
    'main',
    TRUE,
    TRUE
),
(
    1,
    'feature/transmon-calibration',
    FALSE,
    FALSE
);

INSERT INTO contributors (
    username,
    email,
    role_name
)
VALUES
(
    'alice',
    'alice@example.org',
    'quantum-engineer'
),
(
    'bob',
    'bob@example.org',
    'senior-engineer'
),
(
    'carol',
    'carol@example.org',
    'security-reviewer'
);

INSERT INTO reviewers (
    contributor_id,
    security_team,
    senior_engineer
)
VALUES
(
    2,
    FALSE,
    TRUE
),
(
    3,
    TRUE,
    FALSE
);

INSERT INTO commits (
    commit_sha,
    repository_id,
    branch_id,
    author,
    message,
    committed_at
)
VALUES
(
    '1111111111111111111111111111111111111111',
    1,
    1,
    'bob',
    'baseline Josephson circuit model',
    '2026-10-20 09:00:00+05:30'
),
(
    '2222222222222222222222222222222222222222',
    1,
    2,
    'alice',
    'add transmon calibration workflow',
    '2026-10-21 10:00:00+05:30'
),
(
    '3333333333333333333333333333333333333333',
    1,
    2,
    'alice',
    'correct Josephson inductance calculation',
    '2026-10-22 11:00:00+05:30'
);

UPDATE branches
SET head_commit_sha =
    '1111111111111111111111111111111111111111'
WHERE branch_id = 1;

UPDATE branches
SET head_commit_sha =
    '3333333333333333333333333333333333333333'
WHERE branch_id = 2;

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    author_id,
    title,
    description,
    draft,
    state,
    head_commit_sha,
    base_commit_sha
)
VALUES (
    1,
    2,
    1,
    1,
    'Improve transmon calibration model',
    'Adds Josephson energy, anharmonicity, and calibration checks.',
    FALSE,
    'OPEN',
    '3333333333333333333333333333333333333333',
    '1111111111111111111111111111111111111111'
);

INSERT INTO pull_request_commits (
    pull_request_id,
    commit_sha,
    position_no
)
VALUES
(
    1,
    '2222222222222222222222222222222222222222',
    1
),
(
    1,
    '3333333333333333333333333333333333333333',
    2
);

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body,
    commit_sha
)
VALUES (
    1,
    1,
    'APPROVED',
    'Reviewed the circuit equations and calibration changes.',
    '3333333333333333333333333333333333333333'
);

INSERT INTO reviews (
    pull_request_id,
    reviewer_id,
    state,
    body,
    commit_sha
)
VALUES (
    1,
    2,
    'APPROVED',
    'Security and repository-governance review passed.',
    '3333333333333333333333333333333333333333'
);

INSERT INTO review_comments (
    review_id,
    file_path,
    line_number,
    body,
    resolved
)
VALUES (
    1,
    'transmon.py',
    81,
    'Check the sign convention for anharmonicity.',
    TRUE
);

INSERT INTO status_checks (
    pull_request_id,
    check_name,
    state,
    commit_sha,
    completed_at,
    details
)
VALUES
(
    1,
    'unit-tests',
    'PASS',
    '3333333333333333333333333333333333333333',
    CURRENT_TIMESTAMP,
    'All circuit-model tests passed.'
),
(
    1,
    'numerical-stability',
    'PASS',
    '3333333333333333333333333333333333333333',
    CURRENT_TIMESTAMP,
    'RCSJ integration remained finite.'
),
(
    1,
    'security-scan',
    'PASS',
    '3333333333333333333333333333333333333333',
    CURRENT_TIMESTAMP,
    'No repository-policy violations detected.'
);

INSERT INTO branch_protection_policies (
    branch_id,
    required_reviews,
    dismiss_stale_reviews,
    require_status_checks,
    allow_direct_push,
    allow_force_push,
    allow_branch_deletion,
    require_conversation_resolution,
    require_linear_history,
    allow_administrator_bypass
)
VALUES (
    1,
    2,
    TRUE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    TRUE,
    FALSE
);

INSERT INTO approval_requirements (
    policy_id,
    reviewer_role,
    required_count
)
VALUES
(
    1,
    'senior-engineer',
    1
),
(
    1,
    'security-reviewer',
    1
);

INSERT INTO circuits (
    repository_id,
    name,
    component_type,
    state,
    critical_current_a,
    capacitance_f,
    normal_resistance_ohm,
    charging_energy_j
)
VALUES (
    1,
    'transmon-q0',
    'TRANSMON',
    'CALIBRATED',
    35e-9,
    80e-15,
    1500,
    2.0e-24
);

INSERT INTO circuits (
    repository_id,
    name,
    component_type,
    state,
    critical_current_a,
    capacitance_f,
    normal_resistance_ohm,
    loop_inductance_h
)
VALUES (
    1,
    'readout-squid-q0',
    'RF_SQUID',
    'CHARACTERIZED',
    35e-9,
    80e-15,
    1500,
    12e-9
);

INSERT INTO qubit_measurements (
    circuit_id,
    basis,
    shots,
    zero_count,
    one_count
)
VALUES (
    1,
    'Z',
    1000,
    497,
    503
);

CREATE OR REPLACE FUNCTION josephson_energy(
    p_critical_current DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT
        (6.62607015e-34 / (2.0 * 1.602176634e-19))
        * p_critical_current
        / (2.0 * pi());
$$;

CREATE OR REPLACE FUNCTION josephson_inductance(
    p_critical_current DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT
        (6.62607015e-34 / (2.0 * 1.602176634e-19))
        / (2.0 * pi() * p_critical_current);
$$;

CREATE OR REPLACE FUNCTION transmon_f01(
    p_critical_current DOUBLE PRECISION,
    p_charging_energy DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT
        sqrt(
            8.0
            * josephson_energy(p_critical_current)
            * p_charging_energy
        )
        / 6.62607015e-34
        - p_charging_energy / 6.62607015e-34;
$$;

CREATE OR REPLACE FUNCTION evaluate_merge_eligibility(
    p_pull_request_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    target_branch BIGINT;
    required_reviews INTEGER;
    require_checks BOOLEAN;
    require_conversations BOOLEAN;
    approval_count INTEGER;
    passing_checks INTEGER;
    unresolved_comments INTEGER;
    eligible BOOLEAN;
    decision_reason TEXT;
BEGIN
    SELECT
        pr.target_branch_id,
        bp.required_reviews,
        bp.require_status_checks,
        bp.require_conversation_resolution
    INTO
        target_branch,
        required_reviews,
        require_checks,
        require_conversations
    FROM pull_requests pr
    JOIN branch_protection_policies bp
      ON bp.branch_id = pr.target_branch_id
    WHERE pr.pull_request_id = p_pull_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'No protected branch policy exists for PR %',
            p_pull_request_id;
    END IF;

    SELECT count(*)
    INTO approval_count
    FROM reviews r
    JOIN pull_requests pr
      ON pr.pull_request_id = r.pull_request_id
    WHERE r.pull_request_id = p_pull_request_id
      AND r.state = 'APPROVED'
      AND r.commit_sha = pr.head_commit_sha;

    SELECT count(*)
    INTO passing_checks
    FROM status_checks sc
    JOIN pull_requests pr
      ON pr.pull_request_id = sc.pull_request_id
    WHERE sc.pull_request_id = p_pull_request_id
      AND sc.state = 'PASS'
      AND sc.commit_sha = pr.head_commit_sha;

    SELECT count(*)
    INTO unresolved_comments
    FROM review_comments rc
    JOIN reviews r
      ON r.review_id = rc.review_id
    WHERE r.pull_request_id = p_pull_request_id
      AND rc.resolved = FALSE;

    eligible :=
        approval_count >= required_reviews
        AND (
            NOT require_checks
            OR passing_checks >= 1
        )
        AND (
            NOT require_conversations
            OR unresolved_comments = 0
        );

    decision_reason :=
        CASE
            WHEN eligible
            THEN 'All configured merge conditions satisfied.'
            WHEN approval_count < required_reviews
            THEN 'Required approvals are missing.'
            WHEN require_checks AND passing_checks = 0
            THEN 'No passing status check exists for current head.'
            WHEN require_conversations AND unresolved_comments > 0
            THEN 'Unresolved review conversations remain.'
            ELSE 'Merge blocked by repository policy.'
        END;

    INSERT INTO merge_eligibility (
        pull_request_id,
        eligible,
        approval_count,
        passing_check_count,
        unresolved_comment_count,
        reason
    )
    VALUES (
        p_pull_request_id,
        eligible,
        approval_count,
        passing_checks,
        unresolved_comments,
        decision_reason
    )
    ON CONFLICT (pull_request_id)
    DO UPDATE SET
        eligible = EXCLUDED.eligible,
        approval_count = EXCLUDED.approval_count,
        passing_check_count = EXCLUDED.passing_check_count,
        unresolved_comment_count =
            EXCLUDED.unresolved_comment_count,
        reason = EXCLUDED.reason,
        evaluated_at = CURRENT_TIMESTAMP;

    RETURN eligible;
END;
$$;

CREATE OR REPLACE FUNCTION prevent_unprotected_direct_merge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.state = 'MERGED' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM merge_eligibility me
            WHERE me.pull_request_id = NEW.pull_request_id
              AND me.eligible = TRUE
        ) THEN
            RAISE EXCEPTION
                'Pull Request % is not merge-eligible',
                NEW.pull_request_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_unprotected_direct_merge
BEFORE UPDATE OF state
ON pull_requests
FOR EACH ROW
EXECUTE FUNCTION prevent_unprotected_direct_merge();

BEGIN;

SELECT evaluate_merge_eligibility(1);

UPDATE pull_requests
SET state = CASE
    WHEN EXISTS (
        SELECT 1
        FROM merge_eligibility
        WHERE pull_request_id = 1
          AND eligible = TRUE
    )
    THEN 'ELIGIBLE'::merge_state
    ELSE 'BLOCKED'::merge_state
END,
updated_at = CURRENT_TIMESTAMP
WHERE pull_request_id = 1;

COMMIT;

SELECT
    pr.pull_request_id,
    r.name AS repository,
    sb.name AS source_branch,
    tb.name AS target_branch,
    pr.state,
    pr.draft,
    pr.head_commit_sha
FROM pull_requests pr
JOIN repositories r
  ON r.repository_id = pr.repository_id
JOIN branches sb
  ON sb.branch_id = pr.source_branch_id
JOIN branches tb
  ON tb.branch_id = pr.target_branch_id
ORDER BY pr.pull_request_id;

SELECT
    pr.pull_request_id,
    me.eligible,
    me.approval_count,
    me.passing_check_count,
    me.unresolved_comment_count,
    me.reason
FROM merge_eligibility me
JOIN pull_requests pr
  ON pr.pull_request_id = me.pull_request_id;

SELECT
    c.name,
    c.component_type,
    c.state,
    c.critical_current_a,
    c.capacitance_f,
    c.loop_inductance_h,
    CASE
        WHEN c.critical_current_a IS NOT NULL
        THEN josephson_energy(c.critical_current_a)
    END AS josephson_energy_j
FROM circuits c
ORDER BY c.circuit_id;

SELECT
    c.name,
    qm.basis,
    qm.shots,
    qm.zero_count,
    qm.one_count,
    round(
        qm.zero_count::numeric / qm.shots,
        6
    ) AS zero_probability,
    round(
        qm.one_count::numeric / qm.shots,
        6
    ) AS one_probability
FROM qubit_measurements qm
JOIN circuits c
  ON c.circuit_id = qm.circuit_id;

WITH review_status AS (
    SELECT
        pr.pull_request_id,
        count(*) FILTER (
            WHERE r.state = 'APPROVED'
        ) AS approvals,
        count(*) FILTER (
            WHERE r.state = 'CHANGES_REQUESTED'
        ) AS requested_changes,
        count(*) FILTER (
            WHERE r.state <> 'DISMISSED'
        ) AS active_reviews
    FROM pull_requests pr
    LEFT JOIN reviews r
      ON r.pull_request_id = pr.pull_request_id
    GROUP BY pr.pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.title,
    rs.approvals,
    rs.requested_changes,
    rs.active_reviews,
    me.eligible,
    me.reason
FROM pull_requests pr
JOIN review_status rs
  ON rs.pull_request_id = pr.pull_request_id
LEFT JOIN merge_eligibility me
  ON me.pull_request_id = pr.pull_request_id;

SELECT
    bp.policy_id,
    b.name AS protected_branch,
    bp.required_reviews,
    bp.require_status_checks,
    bp.allow_direct_push,
    bp.allow_force_push,
    bp.allow_branch_deletion,
    bp.require_conversation_resolution,
    bp.require_linear_history,
    bp.allow_administrator_bypass
FROM branch_protection_policies bp
JOIN branches b
  ON b.branch_id = bp.branch_id;

SELECT
    c.name,
    c.critical_current_a,
    c.capacitance_f,
    c.charging_energy_j,
    transmon_f01(
        c.critical_current_a,
        c.charging_energy_j
    ) AS approximate_f01_hz
FROM circuits c
WHERE c.component_type = 'TRANSMON'
  AND c.critical_current_a IS NOT NULL
  AND c.charging_energy_j IS NOT NULL;

-- Failure-case query: identify Pull Requests with missing approvals.
SELECT
    pr.pull_request_id,
    pr.title,
    bp.required_reviews,
    COALESCE(me.approval_count, 0) AS approvals,
    CASE
        WHEN COALESCE(me.approval_count, 0)
             < bp.required_reviews
        THEN 'BLOCKED'
        ELSE 'APPROVED'
    END AS approval_status
FROM pull_requests pr
JOIN branch_protection_policies bp
  ON bp.branch_id = pr.target_branch_id
LEFT JOIN merge_eligibility me
  ON me.pull_request_id = pr.pull_request_id;

-- Failure-case query: identify failed or pending automated checks.
SELECT
    pr.pull_request_id,
    pr.title,
    sc.check_name,
    sc.state,
    sc.details
FROM status_checks sc
JOIN pull_requests pr
  ON pr.pull_request_id = sc.pull_request_id
WHERE sc.state IN ('FAIL', 'PENDING')
ORDER BY pr.pull_request_id, sc.check_name;
