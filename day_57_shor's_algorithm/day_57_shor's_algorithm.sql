DROP SCHEMA IF EXISTS shor_lab CASCADE;
CREATE SCHEMA shor_lab;

SET search_path = shor_lab, public;

-- Integer factorization is represented as a workflow:
-- input -> base selection -> gcd preprocessing -> order finding
-- -> period validation -> factor extraction -> final result.

CREATE TYPE factorization_status AS ENUM (
    'RECEIVED',
    'PREPROCESSED',
    'ORDER_SEARCH',
    'PERIOD_FOUND',
    'FACTORED',
    'PRIME',
    'RETRY_REQUIRED',
    'FAILED'
);

CREATE TYPE order_method AS ENUM (
    'CLASSICAL_REFERENCE',
    'QUANTUM_PERIOD_FINDING'
);

CREATE TABLE repositories (
    repository_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_name TEXT NOT NULL UNIQUE,
    default_branch TEXT NOT NULL DEFAULT 'main',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(trim(repository_name)) >= 2),
    CHECK (length(trim(default_branch)) >= 1)
);

CREATE TABLE factoring_jobs (
    job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    repository_id BIGINT REFERENCES repositories(repository_id)
        ON DELETE SET NULL,
    n NUMERIC(100, 0) NOT NULL,
    status factorization_status NOT NULL DEFAULT 'RECEIVED',
    order_method order_method NOT NULL,
    max_attempts INTEGER NOT NULL DEFAULT 32,
    attempts_used INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (n >= 2),
    CHECK (max_attempts BETWEEN 1 AND 10000),
    CHECK (attempts_used BETWEEN 0 AND max_attempts),
    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE TABLE factoring_attempts (
    attempt_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES factoring_jobs(job_id)
        ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    base_a NUMERIC(100, 0) NOT NULL,
    gcd_value NUMERIC(100, 0),
    period_r NUMERIC(100, 0),
    period_even BOOLEAN,
    period_valid BOOLEAN,
    factor_left NUMERIC(100, 0),
    factor_right NUMERIC(100, 0),
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, attempt_number),
    CHECK (attempt_number >= 1),
    CHECK (base_a >= 2),
    CHECK (gcd_value IS NULL OR gcd_value >= 1),
    CHECK (period_r IS NULL OR period_r > 0),
    CHECK (
        (factor_left IS NULL AND factor_right IS NULL)
        OR (
            factor_left > 1
            AND factor_right > 1
            AND factor_left <= factor_right
        )
    )
);

CREATE TABLE factorization_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    job_id BIGINT NOT NULL UNIQUE REFERENCES factoring_jobs(job_id)
        ON DELETE CASCADE,
    factor_left NUMERIC(100, 0),
    factor_right NUMERIC(100, 0),
    is_prime BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (
            is_prime = TRUE
            AND factor_left IS NULL
            AND factor_right IS NULL
        )
        OR (
            is_prime = FALSE
            AND factor_left IS NOT NULL
            AND factor_right IS NOT NULL
            AND factor_left > 1
            AND factor_right > 1
            AND factor_left <= factor_right
        )
    )
);

CREATE INDEX idx_factoring_jobs_status
    ON factoring_jobs(status);

CREATE INDEX idx_factoring_attempts_job
    ON factoring_attempts(job_id);

CREATE INDEX idx_factoring_attempts_period
    ON factoring_attempts(job_id, period_valid)
    WHERE period_valid = TRUE;

CREATE OR REPLACE FUNCTION gcd_numeric(a NUMERIC, b NUMERIC)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    x NUMERIC := abs(a);
    y NUMERIC := abs(b);
    remainder NUMERIC;
BEGIN
    WHILE y <> 0 LOOP
        remainder := mod(x, y);
        x := y;
        y := remainder;
    END LOOP;

    RETURN x;
END;
$$;

CREATE OR REPLACE FUNCTION mod_pow_numeric(
    p_base NUMERIC,
    p_exponent NUMERIC,
    p_modulus NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    base_value NUMERIC := mod(p_base, p_modulus);
    exponent_value NUMERIC := p_exponent;
    result_value NUMERIC := 1;
BEGIN
    IF p_modulus <= 0 THEN
        RAISE EXCEPTION 'Modulus must be positive';
    END IF;

    IF p_exponent < 0 THEN
        RAISE EXCEPTION 'Negative exponents are not supported by this function';
    END IF;

    WHILE exponent_value > 0 LOOP
        IF mod(exponent_value, 2) = 1 THEN
            result_value := mod(
                result_value * base_value,
                p_modulus
            );
        END IF;

        base_value := mod(
            base_value * base_value,
            p_modulus
        );

        exponent_value := floor(exponent_value / 2);
    END LOOP;

    RETURN result_value;
END;
$$;

CREATE OR REPLACE FUNCTION validate_attempt()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    job_n NUMERIC;
BEGIN
    SELECT n
    INTO job_n
    FROM factoring_jobs
    WHERE job_id = NEW.job_id;

    IF job_n IS NULL THEN
        RAISE EXCEPTION 'Unknown factoring job %', NEW.job_id;
    END IF;

    IF NEW.gcd_value IS NOT NULL
       AND NEW.gcd_value <> gcd_numeric(NEW.base_a, job_n) THEN
        RAISE EXCEPTION
            'gcd_value does not match gcd(base_a, n)';
    END IF;

    IF NEW.period_r IS NOT NULL
       AND NEW.period_valid IS DISTINCT FROM (
            mod_pow_numeric(NEW.base_a, NEW.period_r, job_n) = 1
       ) THEN
        RAISE EXCEPTION
            'period_valid does not match modular order validation';
    END IF;

    IF NEW.period_r IS NOT NULL THEN
        NEW.period_even := mod(NEW.period_r, 2) = 0;
    END IF;

    IF NEW.factor_left IS NOT NULL
       AND NEW.factor_right IS NOT NULL
       AND NEW.factor_left * NEW.factor_right <> job_n THEN
        RAISE EXCEPTION
            'Recovered factors do not multiply to job n';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_attempt
BEFORE INSERT OR UPDATE ON factoring_attempts
FOR EACH ROW
EXECUTE FUNCTION validate_attempt();

CREATE OR REPLACE FUNCTION enforce_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    job_n NUMERIC;
BEGIN
    SELECT n INTO job_n
    FROM factoring_jobs
    WHERE job_id = NEW.job_id;

    IF NEW.is_prime THEN
        IF NOT EXISTS (
            SELECT 1
            FROM factoring_jobs
            WHERE job_id = NEW.job_id
              AND status = 'PRIME'
        ) THEN
            RAISE EXCEPTION
                'Prime result requires the job to have PRIME status';
        END IF;
    ELSE
        IF NEW.factor_left * NEW.factor_right <> job_n THEN
            RAISE EXCEPTION
                'Result factors do not multiply to n';
        END IF;

        IF NEW.factor_left <= 1
           OR NEW.factor_right <= 1
           OR NEW.factor_left >= job_n
           OR NEW.factor_right >= job_n THEN
            RAISE EXCEPTION
                'Factors must be non-trivial';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_result
BEFORE INSERT OR UPDATE ON factorization_results
FOR EACH ROW
EXECUTE FUNCTION enforce_result();

CREATE OR REPLACE FUNCTION factor_from_period(
    p_n NUMERIC,
    p_a NUMERIC,
    p_r NUMERIC
)
RETURNS TABLE (
    factor_left NUMERIC,
    factor_right NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    half_power NUMERIC;
    left_factor NUMERIC;
    right_factor NUMERIC;
BEGIN
    IF p_r <= 0 OR mod(p_r, 2) <> 0 THEN
        RETURN;
    END IF;

    half_power := mod_pow_numeric(
        p_a,
        floor(p_r / 2),
        p_n
    );

    IF half_power = p_n - 1 THEN
        RETURN;
    END IF;

    left_factor := gcd_numeric(
        half_power - 1,
        p_n
    );

    right_factor := gcd_numeric(
        half_power + 1,
        p_n
    );

    IF left_factor > 1
       AND right_factor > 1
       AND left_factor < p_n
       AND right_factor < p_n
       AND left_factor * right_factor = p_n THEN

        factor_left := LEAST(left_factor, right_factor);
        factor_right := GREATEST(left_factor, right_factor);

        RETURN NEXT;
    END IF;
END;
$$;

CREATE OR REPLACE VIEW successful_periods AS
SELECT
    a.attempt_id,
    a.job_id,
    j.n,
    a.attempt_number,
    a.base_a,
    a.period_r,
    a.factor_left,
    a.factor_right
FROM factoring_attempts a
JOIN factoring_jobs j
  ON j.job_id = a.job_id
WHERE a.period_valid = TRUE
  AND a.period_even = TRUE;

CREATE OR REPLACE VIEW job_eligibility AS
SELECT
    j.job_id,
    j.n,
    j.status,
    j.attempts_used,
    EXISTS (
        SELECT 1
        FROM factoring_attempts a
        WHERE a.job_id = j.job_id
          AND a.period_valid = TRUE
          AND a.period_even = TRUE
    ) AS has_valid_even_period,
    EXISTS (
        SELECT 1
        FROM factorization_results r
        WHERE r.job_id = j.job_id
          AND r.is_prime = FALSE
    ) AS has_factorization_result
FROM factoring_jobs j;

INSERT INTO repositories (repository_name, default_branch)
VALUES
    ('quantum-number-theory-lab', 'main'),
    ('cryptography-research', 'main');

INSERT INTO factoring_jobs (
    repository_id,
    n,
    status,
    order_method,
    max_attempts,
    attempts_used,
    started_at
)
VALUES
    (
        1,
        15,
        'ORDER_SEARCH',
        'QUANTUM_PERIOD_FINDING',
        16,
        2,
        CURRENT_TIMESTAMP
    ),
    (
        1,
        21,
        'FACTORED',
        'QUANTUM_PERIOD_FINDING',
        16,
        1,
        CURRENT_TIMESTAMP - INTERVAL '5 minutes'
    ),
    (
        2,
        35,
        'RETRY_REQUIRED',
        'QUANTUM_PERIOD_FINDING',
        16,
        3,
        CURRENT_TIMESTAMP - INTERVAL '10 minutes'
    ),
    (
        2,
        13,
        'PRIME',
        'CLASSICAL_REFERENCE',
        1,
        0,
        CURRENT_TIMESTAMP - INTERVAL '20 minutes'
    );

INSERT INTO factoring_attempts (
    job_id,
    attempt_number,
    base_a,
    gcd_value,
    period_r,
    period_valid,
    factor_left,
    factor_right,
    failure_reason
)
VALUES
    (1, 1, 2, 1, 4, TRUE, 3, 5, NULL),
    (1, 2, 7, 1, 4, TRUE, 3, 5, NULL),
    (2, 1, 2, 1, 6, TRUE, 3, 7, NULL),
    (3, 1, 2, 1, 12, FALSE, NULL, NULL,
        'Period candidate failed modular validation'),
    (3, 2, 11, 1, 6, TRUE, NULL, NULL,
        'Valid period but factor extraction policy requires retry'),
    (3, 3, 6, 1, NULL, NULL, NULL, NULL,
        'Base did not produce a usable order');

INSERT INTO factorization_results (
    job_id,
    factor_left,
    factor_right,
    is_prime
)
VALUES
    (2, 3, 7, FALSE),
    (4, NULL, NULL, TRUE);

UPDATE factoring_jobs
SET
    status = 'FACTORED',
    attempts_used = 2,
    completed_at = CURRENT_TIMESTAMP
WHERE job_id = 1;

UPDATE factoring_jobs
SET
    completed_at = CURRENT_TIMESTAMP
WHERE job_id = 2;

-- Retrieval: show jobs and their current workflow state.
SELECT
    job_id,
    n,
    status,
    order_method,
    attempts_used,
    max_attempts
FROM factoring_jobs
ORDER BY job_id;

-- Validation: verify every stored attempt's gcd.
SELECT
    a.attempt_id,
    a.job_id,
    a.base_a,
    a.gcd_value,
    gcd_numeric(a.base_a, j.n) AS calculated_gcd,
    a.gcd_value = gcd_numeric(a.base_a, j.n) AS gcd_is_correct
FROM factoring_attempts a
JOIN factoring_jobs j
  ON j.job_id = a.job_id
ORDER BY a.job_id, a.attempt_number;

-- Evaluation: inspect valid even periods that can participate in
-- classical factor extraction.
SELECT
    job_id,
    n,
    attempt_number,
    base_a,
    period_r,
    factor_left,
    factor_right
FROM successful_periods
ORDER BY job_id, attempt_number;

-- Recompute factors directly from an observed period.
SELECT
    j.job_id,
    j.n,
    a.base_a,
    a.period_r,
    f.factor_left,
    f.factor_right
FROM factoring_jobs j
JOIN factoring_attempts a
  ON a.job_id = j.job_id
CROSS JOIN LATERAL factor_from_period(
    j.n,
    a.base_a,
    a.period_r
) f
ORDER BY j.job_id;

-- Aggregation: summarize attempts and successful periods per job.
SELECT
    j.job_id,
    j.n,
    COUNT(a.attempt_id) AS attempts,
    COUNT(a.attempt_id) FILTER (
        WHERE a.period_valid = TRUE
    ) AS valid_periods,
    COUNT(a.attempt_id) FILTER (
        WHERE a.period_valid = TRUE
          AND a.period_even = TRUE
    ) AS valid_even_periods
FROM factoring_jobs j
LEFT JOIN factoring_attempts a
  ON a.job_id = j.job_id
GROUP BY j.job_id, j.n
ORDER BY j.job_id;

-- Workflow report: distinguish "a valid period exists" from
-- "the repository has a committed final factorization result".
SELECT
    job_id,
    n,
    status,
    attempts_used,
    has_valid_even_period,
    has_factorization_result,
    CASE
        WHEN has_factorization_result THEN 'FACTORED'
        WHEN status = 'PRIME' THEN 'PRIME'
        WHEN has_valid_even_period THEN 'FACTOR_EXTRACTION_AVAILABLE'
        WHEN attempts_used >= (
            SELECT max_attempts
            FROM factoring_jobs j2
            WHERE j2.job_id = job_eligibility.job_id
        ) THEN 'RETRY_LIMIT_REACHED'
        ELSE 'ORDER_SEARCH_REQUIRED'
    END AS workflow_decision
FROM job_eligibility
ORDER BY job_id;

-- Transactional demonstration: an attempt and its job state are changed
-- atomically. The savepoint makes the failure path explicit.
BEGIN;

SAVEPOINT before_invalid_transition;

UPDATE factoring_jobs
SET
    status = 'PERIOD_FOUND',
    attempts_used = attempts_used + 1
WHERE job_id = 3;

-- A period-found state is useful only after a valid period exists.
UPDATE factoring_jobs
SET status = CASE
    WHEN EXISTS (
        SELECT 1
        FROM factoring_attempts
        WHERE job_id = 3
          AND period_valid = TRUE
          AND period_even = TRUE
    )
    THEN 'PERIOD_FOUND'
    ELSE 'RETRY_REQUIRED'
END
WHERE job_id = 3;

RELEASE SAVEPOINT before_invalid_transition;

COMMIT;

-- Security and integrity properties:
-- 1. Numeric constraints reject invalid n and factor values.
-- 2. Foreign keys prevent orphaned attempts and results.
-- 3. Triggers validate stored mathematical relationships.
-- 4. The schema does not store private credentials or external secrets.
-- 5. NUMERIC is used so database arithmetic is not limited to 64-bit integers.
