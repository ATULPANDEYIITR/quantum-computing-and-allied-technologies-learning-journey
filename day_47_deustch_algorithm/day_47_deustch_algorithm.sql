-- PostgreSQL 15+
-- Deutsch algorithm: reproducible oracle truth tables, mathematical
-- circuit outcomes, query-complexity comparison, and an isolated
-- repository-governance policy example.
--
-- The repository tables are not quantum components. They demonstrate
-- that the mathematical oracle classification and merge authorization
-- are different domains and must not be conflated.

BEGIN;

DROP VIEW IF EXISTS deutsch_oracle_results CASCADE;
DROP VIEW IF EXISTS pull_request_merge_eligibility CASCADE;
DROP TABLE IF EXISTS repository_reviews CASCADE;
DROP TABLE IF EXISTS required_status_checks CASCADE;
DROP TABLE IF EXISTS pull_request_commits CASCADE;
DROP TABLE IF EXISTS pull_requests CASCADE;
DROP TABLE IF EXISTS branch_protection_policies CASCADE;
DROP TABLE IF EXISTS repository_branches CASCADE;
DROP TABLE IF EXISTS repository_members CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS deutsch_oracles CASCADE;

CREATE TABLE deutsch_oracles (
    oracle_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    oracle_name     TEXT NOT NULL UNIQUE,
    f_zero          SMALLINT NOT NULL CHECK (f_zero IN (0, 1)),
    f_one           SMALLINT NOT NULL CHECK (f_one IN (0, 1)),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO deutsch_oracles (oracle_name, f_zero, f_one)
VALUES
    ('zero_function', 0, 0),
    ('identity_function', 0, 1),
    ('negation_function', 1, 0),
    ('one_function', 1, 1);

-- The promise problem is encoded directly as a derived classification.
-- The parity of the truth-table outputs determines the final input bit:
-- equal outputs imply constant; unequal outputs imply balanced.
CREATE VIEW deutsch_oracle_results AS
SELECT
    oracle_id,
    oracle_name,
    f_zero,
    f_one,
    CASE
        WHEN f_zero = f_one THEN 'constant'
        ELSE 'balanced'
    END AS classification,
    CASE
        WHEN f_zero = f_one THEN 1.0::NUMERIC
        ELSE 0.0::NUMERIC
    END AS probability_input_zero,
    CASE
        WHEN f_zero <> f_one THEN 1.0::NUMERIC
        ELSE 0.0::NUMERIC
    END AS probability_input_one,
    1 AS quantum_oracle_calls,
    2 AS classical_deterministic_worst_case_calls
FROM deutsch_oracles;

CREATE TABLE repositories (
    repository_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch  TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) > 0),
    CHECK (length(trim(default_branch)) > 0)
);

CREATE TABLE repository_branches (
    branch_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id   BIGINT NOT NULL REFERENCES repositories(repository_id)
                    ON DELETE CASCADE,
    branch_name     TEXT NOT NULL,
    is_protected    BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (repository_id, branch_name),
    CHECK (length(trim(branch_name)) > 0)
);

CREATE TABLE repository_members (
    member_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id   BIGINT NOT NULL REFERENCES repositories(repository_id)
                    ON DELETE CASCADE,
    username        TEXT NOT NULL,
    can_review      BOOLEAN NOT NULL DEFAULT TRUE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (repository_id, username),
    CHECK (length(trim(username)) > 0)
);

CREATE TABLE branch_protection_policies (
    policy_id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    branch_id                       BIGINT NOT NULL UNIQUE
                                    REFERENCES repository_branches(branch_id)
                                    ON DELETE CASCADE,
    required_approvals              INTEGER NOT NULL DEFAULT 1
                                    CHECK (required_approvals BETWEEN 0 AND 20),
    require_passing_checks          BOOLEAN NOT NULL DEFAULT TRUE,
    require_resolved_conversations  BOOLEAN NOT NULL DEFAULT TRUE,
    require_linear_history          BOOLEAN NOT NULL DEFAULT FALSE,
    restrict_direct_pushes          BOOLEAN NOT NULL DEFAULT TRUE,
    prevent_force_push              BOOLEAN NOT NULL DEFAULT TRUE,
    prevent_deletion                BOOLEAN NOT NULL DEFAULT TRUE,
    dismiss_stale_approvals         BOOLEAN NOT NULL DEFAULT TRUE,
    allow_admin_bypass              BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_merge_strategies       TEXT[] NOT NULL
                                    DEFAULT ARRAY['squash', 'rebase']::TEXT[],
    CHECK (cardinality(allowed_merge_strategies) > 0)
);

CREATE TABLE pull_requests (
    pull_request_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id       BIGINT NOT NULL REFERENCES repositories(repository_id),
    source_branch_id    BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    target_branch_id    BIGINT NOT NULL REFERENCES repository_branches(branch_id),
    title               TEXT NOT NULL,
    author_member_id    BIGINT NOT NULL REFERENCES repository_members(member_id),
    lifecycle_state     TEXT NOT NULL DEFAULT 'open'
                        CHECK (lifecycle_state IN (
                            'draft', 'open', 'closed', 'merged'
                        )),
    base_synchronized   BOOLEAN NOT NULL DEFAULT FALSE,
    has_merge_conflicts BOOLEAN NOT NULL DEFAULT FALSE,
    conversations_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    linear_history_satisfied BOOLEAN NOT NULL DEFAULT FALSE,
    merge_strategy      TEXT NOT NULL DEFAULT 'squash'
                        CHECK (merge_strategy IN (
                            'merge_commit', 'squash', 'rebase'
                        )),
    opened_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at           TIMESTAMPTZ,
    CHECK (source_branch_id <> target_branch_id),
    CHECK (length(trim(title)) > 0),
    CHECK (
        (lifecycle_state IN ('closed', 'merged') AND closed_at IS NOT NULL)
        OR
        (lifecycle_state IN ('draft', 'open') AND closed_at IS NULL)
    )
);

CREATE TABLE pull_request_commits (
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
                    ON DELETE CASCADE,
    commit_sha      CHAR(40) NOT NULL,
    committed_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pull_request_id, commit_sha),
    CHECK (commit_sha ~ '^[0-9a-f]{40}$')
);

CREATE TABLE required_status_checks (
    status_check_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
                    ON DELETE CASCADE,
    check_name      TEXT NOT NULL,
    check_state     TEXT NOT NULL
                    CHECK (check_state IN ('pending', 'passed', 'failed')),
    commit_sha      CHAR(40),
    completed_at    TIMESTAMPTZ,
    UNIQUE (pull_request_id, check_name),
    CHECK (length(trim(check_name)) > 0),
    CHECK (
        (check_state = 'pending' AND completed_at IS NULL)
        OR
        (check_state IN ('passed', 'failed') AND completed_at IS NOT NULL)
    ),
    CHECK (commit_sha IS NULL OR commit_sha ~ '^[0-9a-f]{40}$')
);

CREATE TABLE repository_reviews (
    review_id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pull_request_id     BIGINT NOT NULL REFERENCES pull_requests(pull_request_id)
                        ON DELETE CASCADE,
    reviewer_member_id  BIGINT NOT NULL REFERENCES repository_members(member_id),
    review_state        TEXT NOT NULL
                        CHECK (review_state IN (
                            'commented', 'approved', 'changes_requested',
                            'dismissed'
                        )),
    commit_sha          CHAR(40),
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stale               BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (pull_request_id, reviewer_member_id),
    CHECK (commit_sha IS NULL OR commit_sha ~ '^[0-9a-f]{40}$')
);

CREATE INDEX idx_pull_requests_target_state
    ON pull_requests (target_branch_id, lifecycle_state);

CREATE INDEX idx_reviews_pull_request_state
    ON repository_reviews (pull_request_id, review_state);

CREATE INDEX idx_status_checks_pull_request_state
    ON required_status_checks (pull_request_id, check_state);

INSERT INTO repositories (repository_name, default_branch)
VALUES ('payment-service', 'main');

INSERT INTO repository_branches
    (repository_id, branch_name, is_protected)
SELECT repository_id, 'main', TRUE
FROM repositories
WHERE repository_name = 'payment-service';

INSERT INTO repository_branches
    (repository_id, branch_name, is_protected)
SELECT repository_id, 'feature/payment-validation', FALSE
FROM repositories
WHERE repository_name = 'payment-service';

INSERT INTO repository_members
    (repository_id, username, can_review, is_active)
SELECT repository_id, 'atul-reviewer', TRUE, TRUE
FROM repositories
WHERE repository_name = 'payment-service';

INSERT INTO repository_members
    (repository_id, username, can_review, is_active)
SELECT repository_id, 'security-reviewer', TRUE, TRUE
FROM repositories
WHERE repository_name = 'payment-service';

INSERT INTO repository_members
    (repository_id, username, can_review, is_active)
SELECT repository_id, 'contributor', FALSE, TRUE
FROM repositories
WHERE repository_name = 'payment-service';

INSERT INTO branch_protection_policies (
    branch_id,
    required_approvals,
    require_passing_checks,
    require_resolved_conversations,
    require_linear_history,
    restrict_direct_pushes,
    prevent_force_push,
    prevent_deletion,
    dismiss_stale_approvals,
    allow_admin_bypass,
    allowed_merge_strategies
)
SELECT
    branch_id,
    2,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE,
    ARRAY['squash', 'rebase']::TEXT[]
FROM repository_branches
WHERE branch_name = 'main'
  AND repository_id = (
      SELECT repository_id
      FROM repositories
      WHERE repository_name = 'payment-service'
  );

INSERT INTO pull_requests (
    repository_id,
    source_branch_id,
    target_branch_id,
    title,
    author_member_id,
    lifecycle_state,
    base_synchronized,
    has_merge_conflicts,
    conversations_resolved,
    linear_history_satisfied,
    merge_strategy
)
SELECT
    repo.repository_id,
    source.branch_id,
    target.branch_id,
    'Validate payment request amounts',
    author.member_id,
    'open',
    TRUE,
    FALSE,
    TRUE,
    TRUE,
    'squash'
FROM repositories repo
JOIN repository_branches source
  ON source.repository_id = repo.repository_id
 AND source.branch_name = 'feature/payment-validation'
JOIN repository_branches target
  ON target.repository_id = repo.repository_id
 AND target.branch_name = 'main'
JOIN repository_members author
  ON author.repository_id = repo.repository_id
 AND author.username = 'contributor'
WHERE repo.repository_name = 'payment-service';

INSERT INTO pull_request_commits (pull_request_id, commit_sha)
SELECT pull_request_id,
       'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
FROM pull_requests
WHERE title = 'Validate payment request amounts';

INSERT INTO required_status_checks (
    pull_request_id,
    check_name,
    check_state,
    commit_sha,
    completed_at
)
SELECT
    pull_request_id,
    'unit-tests',
    'passed',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    CURRENT_TIMESTAMP
FROM pull_requests
WHERE title = 'Validate payment request amounts';

INSERT INTO required_status_checks (
    pull_request_id,
    check_name,
    check_state,
    commit_sha,
    completed_at
)
SELECT
    pull_request_id,
    'security-analysis',
    'passed',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    CURRENT_TIMESTAMP
FROM pull_requests
WHERE title = 'Validate payment request amounts';

INSERT INTO repository_reviews (
    pull_request_id,
    reviewer_member_id,
    review_state,
    commit_sha,
    stale
)
SELECT
    pr.pull_request_id,
    reviewer.member_id,
    'approved',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    FALSE
FROM pull_requests pr
JOIN repositories repo
  ON repo.repository_id = pr.repository_id
JOIN repository_members reviewer
  ON reviewer.repository_id = repo.repository_id
 AND reviewer.username = 'atul-reviewer'
WHERE pr.title = 'Validate payment request amounts';

INSERT INTO repository_reviews (
    pull_request_id,
    reviewer_member_id,
    review_state,
    commit_sha,
    stale
)
SELECT
    pr.pull_request_id,
    reviewer.member_id,
    'approved',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    FALSE
FROM pull_requests pr
JOIN repositories repo
  ON repo.repository_id = pr.repository_id
JOIN repository_members reviewer
  ON reviewer.repository_id = repo.repository_id
 AND reviewer.username = 'security-reviewer'
WHERE pr.title = 'Validate payment request amounts';

-- A reviewer must be active and permitted to review before an approval
-- contributes to merge eligibility. Stale approvals are excluded when the
-- policy dismisses them. A production system should enforce review writes
-- through controlled procedures or application authorization.
CREATE VIEW pull_request_merge_eligibility AS
WITH review_totals AS (
    SELECT
        pr.pull_request_id,
        COUNT(*) FILTER (
            WHERE review.review_state = 'approved'
              AND reviewer.is_active
              AND reviewer.can_review
              AND (
                  NOT policy.dismiss_stale_approvals
                  OR NOT review.stale
              )
        ) AS valid_approvals,
        BOOL_OR(
            review.review_state = 'changes_requested'
            AND reviewer.is_active
            AND reviewer.can_review
            AND (
                NOT policy.dismiss_stale_approvals
                OR NOT review.stale
            )
        ) AS has_active_change_request
    FROM pull_requests pr
    JOIN repository_branches target
      ON target.branch_id = pr.target_branch_id
    JOIN branch_protection_policies policy
      ON policy.branch_id = target.branch_id
    LEFT JOIN repository_reviews review
      ON review.pull_request_id = pr.pull_request_id
    LEFT JOIN repository_members reviewer
      ON reviewer.member_id = review.reviewer_member_id
    GROUP BY pr.pull_request_id
),
check_totals AS (
    SELECT
        pr.pull_request_id,
        COUNT(checks.status_check_id) FILTER (
            WHERE checks.check_state = 'passed'
        ) AS passed_checks,
        COUNT(checks.status_check_id) AS total_checks,
        BOOL_OR(checks.check_state IN ('pending', 'failed')) AS has_bad_check
    FROM pull_requests pr
    LEFT JOIN required_status_checks checks
      ON checks.pull_request_id = pr.pull_request_id
    GROUP BY pr.pull_request_id
)
SELECT
    pr.pull_request_id,
    pr.title,
    repo.repository_name,
    source.branch_name AS source_branch,
    target.branch_name AS target_branch,
    pr.lifecycle_state,
    COALESCE(review_totals.valid_approvals, 0) AS valid_approvals,
    policy.required_approvals,
    COALESCE(check_totals.passed_checks, 0) AS passed_checks,
    COALESCE(check_totals.total_checks, 0) AS total_checks,
    (
        pr.lifecycle_state = 'open'
        AND pr.base_synchronized
        AND NOT pr.has_merge_conflicts
        AND policy.required_approvals
            <= COALESCE(review_totals.valid_approvals, 0)
        AND NOT COALESCE(review_totals.has_active_change_request, FALSE)
        AND (
            NOT policy.require_passing_checks
            OR (
                COALESCE(check_totals.total_checks, 0) > 0
                AND NOT COALESCE(check_totals.has_bad_check, FALSE)
            )
        )
        AND (
            NOT policy.require_resolved_conversations
            OR pr.conversations_resolved
        )
        AND (
            NOT policy.require_linear_history
            OR pr.linear_history_satisfied
        )
        AND pr.merge_strategy = ANY(policy.allowed_merge_strategies)
    ) AS merge_eligible
FROM pull_requests pr
JOIN repositories repo
  ON repo.repository_id = pr.repository_id
JOIN repository_branches source
  ON source.branch_id = pr.source_branch_id
JOIN repository_branches target
  ON target.branch_id = pr.target_branch_id
JOIN branch_protection_policies policy
  ON policy.branch_id = target.branch_id
LEFT JOIN review_totals
  ON review_totals.pull_request_id = pr.pull_request_id
LEFT JOIN check_totals
  ON check_totals.pull_request_id = pr.pull_request_id;

-- Query the quantum promise problem.
SELECT
    oracle_name,
    f_zero,
    f_one,
    classification,
    probability_input_zero,
    probability_input_one,
    quantum_oracle_calls,
    classical_deterministic_worst_case_calls
FROM deutsch_oracle_results
ORDER BY oracle_id;

-- Query repository merge eligibility independently of the quantum result.
SELECT
    repository_name,
    title,
    source_branch,
    target_branch,
    valid_approvals,
    required_approvals,
    passed_checks,
    total_checks,
    merge_eligible
FROM pull_request_merge_eligibility
ORDER BY pull_request_id;

-- An explicit stale approval does not count when the branch policy
-- requires stale approvals to be dismissed.
UPDATE repository_reviews
SET stale = TRUE
WHERE review_id = (
    SELECT MIN(review_id)
    FROM repository_reviews
);

SELECT
    title,
    valid_approvals,
    required_approvals,
    merge_eligible
FROM pull_request_merge_eligibility;

-- Demonstrate that a pending check blocks eligibility. The transaction
-- is rolled back so the original passing fixture remains reproducible.
SAVEPOINT before_pending_check;

UPDATE required_status_checks
SET check_state = 'pending',
    completed_at = NULL
WHERE check_name = 'security-analysis';

SELECT
    title,
    merge_eligible
FROM pull_request_merge_eligibility;

ROLLBACK TO SAVEPOINT before_pending_check;

-- Integrity failures should be tested independently by attempting, for
-- example, to insert a truth-table output of 2 or a negative approval
-- requirement. PostgreSQL CHECK constraints reject those writes.
-- Direct pushes, force pushes, deletion, administrator bypass, merge
-- execution, and review authorization require actual enforcement logic;
-- storing policy flags alone does not enforce repository permissions.

ROLLBACK;
