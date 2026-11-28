-- =========================================================
-- HYBRID QUANTUM-CLASSICAL MACHINE LEARNING
-- PostgreSQL 15+
--
-- Relational experiment-management platform.
--
-- Models:
--   Organizations
--   Users and execution roles
--   Datasets
--   Quantum backends
--   Hybrid models
--   Experiments
--   Training runs
--   Quantum circuit executions
--   Classical optimization steps
--   Evaluation metrics
--   Execution policies
--   Model governance
--
-- Quantum simulation and hardware execution are performed
-- by external execution services. PostgreSQL manages their
-- metadata, authorization, lifecycle, and results.
-- =========================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS hybrid_ml;

SET search_path TO hybrid_ml, public;


-- =========================================================
-- ENUM TYPES
-- =========================================================

CREATE TYPE execution_mode AS ENUM (
    'simulator',
    'quantum_hardware',
    'classical_fallback'
);

CREATE TYPE experiment_status AS ENUM (
    'created',
    'validating',
    'queued',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE model_type AS ENUM (
    'quantum_kernel',
    'variational_classifier',
    'hybrid_feature_classifier'
);

CREATE TYPE user_role AS ENUM (
    'researcher',
    'operator',
    'reviewer',
    'administrator'
);

CREATE TYPE review_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);

CREATE TYPE run_status AS ENUM (
    'queued',
    'running',
    'completed',
    'failed'
);

CREATE TYPE circuit_status AS ENUM (
    'submitted',
    'executing',
    'completed',
    'failed'
);


-- =========================================================
-- ORGANIZATIONS
-- =========================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- USERS
-- =========================================================

CREATE TABLE research_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    username VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, username)
);


-- =========================================================
-- DATASETS
-- =========================================================

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    dataset_name VARCHAR(150) NOT NULL,
    dataset_version VARCHAR(40) NOT NULL,
    feature_count INTEGER NOT NULL CHECK (feature_count > 0),
    sample_count INTEGER NOT NULL CHECK (sample_count > 0),
    training_samples INTEGER NOT NULL CHECK (training_samples >= 0),
    testing_samples INTEGER NOT NULL CHECK (testing_samples >= 0),
    label_type VARCHAR(40) NOT NULL,
    checksum_sha256 CHAR(64) NOT NULL,
    approved_for_research BOOLEAN NOT NULL DEFAULT FALSE,
    contains_sensitive_data BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, dataset_name, dataset_version),

    CHECK (
        training_samples + testing_samples <= sample_count
    ),

    CHECK (
        checksum_sha256 ~ '^[0-9a-fA-F]{64}$'
    ),

    CHECK (label_type IN ('binary', 'multiclass', 'regression'))
);


-- =========================================================
-- QUANTUM BACKENDS
-- =========================================================

CREATE TABLE quantum_backends (
    backend_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    backend_name VARCHAR(150) NOT NULL UNIQUE,
    execution_mode execution_mode NOT NULL,
    provider_name VARCHAR(150),
    maximum_qubits INTEGER NOT NULL CHECK (maximum_qubits > 0),
    supports_shots BOOLEAN NOT NULL DEFAULT TRUE,
    supports_noise_model BOOLEAN NOT NULL DEFAULT FALSE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- MODEL DEFINITIONS
-- =========================================================

CREATE TABLE models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    model_name VARCHAR(150) NOT NULL,
    model_type model_type NOT NULL,
    description TEXT,
    input_dimension INTEGER NOT NULL CHECK (input_dimension > 0),
    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),
    parameter_count INTEGER NOT NULL CHECK (parameter_count >= 0),
    created_by BIGINT NOT NULL REFERENCES research_users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, model_name)
);


-- =========================================================
-- EXECUTION POLICIES
-- =========================================================

CREATE TABLE execution_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    policy_name VARCHAR(120) NOT NULL,
    minimum_qubits INTEGER NOT NULL DEFAULT 1,
    maximum_qubits INTEGER NOT NULL,
    maximum_shots INTEGER NOT NULL DEFAULT 100000,
    maximum_epochs INTEGER NOT NULL DEFAULT 1000,
    allow_hardware BOOLEAN NOT NULL DEFAULT FALSE,
    allow_fallback BOOLEAN NOT NULL DEFAULT TRUE,
    require_approved_dataset BOOLEAN NOT NULL DEFAULT TRUE,
    require_review BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (organization_id, policy_name),

    CHECK (minimum_qubits > 0),
    CHECK (maximum_qubits >= minimum_qubits),
    CHECK (maximum_shots > 0),
    CHECK (maximum_epochs > 0)
);


-- =========================================================
-- EXPERIMENTS
-- =========================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    experiment_name VARCHAR(180) NOT NULL,

    model_id BIGINT NOT NULL REFERENCES models(model_id),
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    backend_id BIGINT NOT NULL REFERENCES quantum_backends(backend_id),
    policy_id BIGINT NOT NULL REFERENCES execution_policies(policy_id),

    created_by BIGINT NOT NULL REFERENCES research_users(user_id),

    execution_mode execution_mode NOT NULL,
    status experiment_status NOT NULL DEFAULT 'created',

    epochs INTEGER NOT NULL CHECK (epochs > 0),
    learning_rate NUMERIC(12, 8) NOT NULL
        CHECK (learning_rate > 0),

    regularization NUMERIC(12, 8) NOT NULL DEFAULT 0.1
        CHECK (regularization > 0),

    shots INTEGER NOT NULL CHECK (shots > 0),

    random_seed BIGINT NOT NULL,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),

    CHECK (
        completed_at IS NULL
        OR completed_at >= started_at
    ),

    CHECK (
        status <> 'failed'
        OR failure_reason IS NOT NULL
    )
);


-- =========================================================
-- EXPERIMENT REVIEW
-- =========================================================

CREATE TABLE experiment_reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    reviewer_id BIGINT NOT NULL
        REFERENCES research_users(user_id),

    status review_status NOT NULL DEFAULT 'pending',

    review_comment TEXT,

    reviewed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, reviewer_id),

    CHECK (
        status = 'pending'
        OR reviewed_at IS NOT NULL
    )
);


-- =========================================================
-- TRAINING RUNS
-- =========================================================

CREATE TABLE training_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    run_number INTEGER NOT NULL CHECK (run_number > 0),

    status run_status NOT NULL DEFAULT 'queued',

    training_loss NUMERIC(16, 10),
    validation_loss NUMERIC(16, 10),

    completed_epochs INTEGER NOT NULL DEFAULT 0
        CHECK (completed_epochs >= 0),

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, run_number),

    CHECK (
        training_loss IS NULL OR training_loss >= 0
    ),

    CHECK (
        validation_loss IS NULL OR validation_loss >= 0
    ),

    CHECK (
        status <> 'failed' OR error_message IS NOT NULL
    )
);


-- =========================================================
-- QUANTUM CIRCUIT EXECUTIONS
-- =========================================================

CREATE TABLE quantum_circuit_runs (
    circuit_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id)
        ON DELETE CASCADE,

    circuit_name VARCHAR(120) NOT NULL,

    circuit_depth INTEGER NOT NULL CHECK (circuit_depth >= 0),

    qubit_count INTEGER NOT NULL CHECK (qubit_count > 0),

    gate_count INTEGER NOT NULL CHECK (gate_count >= 0),

    shots INTEGER NOT NULL CHECK (shots > 0),

    status circuit_status NOT NULL DEFAULT 'submitted',

    expectation_values JSONB,

    measurement_counts JSONB,

    execution_time_ms NUMERIC(14, 4),

    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CHECK (
        expectation_values IS NULL
        OR jsonb_typeof(expectation_values) = 'array'
    ),

    CHECK (
        measurement_counts IS NULL
        OR jsonb_typeof(measurement_counts) = 'object'
    ),

    CHECK (
        execution_time_ms IS NULL
        OR execution_time_ms >= 0
    ),

    CHECK (
        status <> 'failed'
        OR error_message IS NOT NULL
    )
);


-- =========================================================
-- CLASSICAL OPTIMIZATION HISTORY
-- =========================================================

CREATE TABLE optimization_steps (
    optimization_step_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id)
        ON DELETE CASCADE,

    epoch INTEGER NOT NULL CHECK (epoch > 0),

    optimizer_name VARCHAR(80) NOT NULL,

    learning_rate NUMERIC(12, 8) NOT NULL
        CHECK (learning_rate > 0),

    objective_value NUMERIC(16, 10) NOT NULL,

    gradient_norm NUMERIC(16, 10),

    parameter_vector JSONB NOT NULL,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (run_id, epoch),

    CHECK (objective_value >= 0),

    CHECK (
        gradient_norm IS NULL OR gradient_norm >= 0
    ),

    CHECK (jsonb_typeof(parameter_vector) = 'array')
);


-- =========================================================
-- EVALUATION METRICS
-- =========================================================

CREATE TABLE evaluation_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id)
        ON DELETE CASCADE,

    dataset_partition VARCHAR(30) NOT NULL,

    accuracy NUMERIC(10, 8) NOT NULL,
    precision_score NUMERIC(10, 8) NOT NULL,
    recall_score NUMERIC(10, 8) NOT NULL,
    f1_score NUMERIC(10, 8) NOT NULL,

    true_positive BIGINT NOT NULL DEFAULT 0,
    true_negative BIGINT NOT NULL DEFAULT 0,
    false_positive BIGINT NOT NULL DEFAULT 0,
    false_negative BIGINT NOT NULL DEFAULT 0,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (dataset_partition IN ('training', 'validation', 'testing')),

    CHECK (accuracy BETWEEN 0 AND 1),
    CHECK (precision_score BETWEEN 0 AND 1),
    CHECK (recall_score BETWEEN 0 AND 1),
    CHECK (f1_score BETWEEN 0 AND 1),

    CHECK (
        true_positive >= 0
        AND true_negative >= 0
        AND false_positive >= 0
        AND false_negative >= 0
    ),

    UNIQUE (run_id, dataset_partition)
);


-- =========================================================
-- MODEL DEPLOYMENT APPROVAL
-- =========================================================

CREATE TABLE model_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL REFERENCES models(model_id),

    reviewer_id BIGINT NOT NULL REFERENCES research_users(user_id),

    status review_status NOT NULL DEFAULT 'pending',

    decision_reason TEXT,

    approved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (model_id, reviewer_id),

    CHECK (
        status = 'pending'
        OR approved_at IS NOT NULL
    )
);


-- =========================================================
-- AUDIT LOG
-- =========================================================

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    actor_id BIGINT REFERENCES research_users(user_id),

    action VARCHAR(100) NOT NULL,

    previous_status experiment_status,

    new_status experiment_status,

    details JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX idx_experiments_status
ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_owner
ON experiments(created_by, created_at DESC);

CREATE INDEX idx_experiments_dataset
ON experiments(dataset_id, status);

CREATE INDEX idx_training_runs_experiment
ON training_runs(experiment_id, run_number DESC);

CREATE INDEX idx_circuit_runs_status
ON quantum_circuit_runs(status, submitted_at);

CREATE INDEX idx_optimization_run_epoch
ON optimization_steps(run_id, epoch);

CREATE INDEX idx_metrics_run
ON evaluation_metrics(run_id, dataset_partition);

CREATE INDEX idx_audit_experiment_time
ON experiment_audit(experiment_id, created_at DESC);

CREATE INDEX idx_experiment_reviews_pending
ON experiment_reviews(experiment_id)
WHERE status = 'pending';


-- =========================================================
-- EXPERIMENT AUDIT TRIGGER
-- =========================================================

CREATE OR REPLACE FUNCTION record_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN

        INSERT INTO experiment_audit (
            experiment_id,
            actor_id,
            action,
            previous_status,
            new_status,
            details
        )
        VALUES (
            NEW.experiment_id,
            NEW.created_by,
            'STATUS_CHANGED',
            OLD.status,
            NEW.status,
            jsonb_build_object(
                'experiment_name', NEW.experiment_name
            )
        );

    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_experiment_status
AFTER UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION record_experiment_status();


-- =========================================================
-- EXECUTION ELIGIBILITY FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION check_experiment_eligibility(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    e experiments%ROWTYPE;
    d datasets%ROWTYPE;
    m models%ROWTYPE;
    b quantum_backends%ROWTYPE;
    p execution_policies%ROWTYPE;
    owner_role user_role;
    approved_reviews BIGINT;
BEGIN

    SELECT *
    INTO e
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Experiment does not exist';
        RETURN;
    END IF;

    SELECT * INTO d
    FROM datasets
    WHERE dataset_id = e.dataset_id;

    SELECT * INTO m
    FROM models
    WHERE model_id = e.model_id;

    SELECT * INTO b
    FROM quantum_backends
    WHERE backend_id = e.backend_id;

    SELECT * INTO p
    FROM execution_policies
    WHERE policy_id = e.policy_id;

    IF NOT p.active THEN
        RETURN QUERY SELECT FALSE, 'Execution policy is inactive';
        RETURN;
    END IF;

    IF NOT b.enabled THEN
        RETURN QUERY SELECT FALSE, 'Backend is disabled';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM research_users u
        WHERE u.user_id = e.created_by
          AND u.organization_id = e.organization_id
          AND u.active = TRUE
    ) THEN
        RETURN QUERY SELECT FALSE, 'Experiment owner is inactive or unauthorized';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM research_users u
        WHERE u.user_id = e.created_by
          AND u.organization_id = e.organization_id
    ) THEN
        RETURN QUERY SELECT FALSE, 'Organization ownership mismatch';
        RETURN;
    END IF;

    IF p.require_approved_dataset AND NOT d.approved_for_research THEN
        RETURN QUERY SELECT FALSE, 'Dataset approval is required';
        RETURN;
    END IF;

    IF d.contains_sensitive_data AND NOT d.approved_for_research THEN
        RETURN QUERY SELECT FALSE, 'Sensitive dataset is not approved';
        RETURN;
    END IF;

    IF m.organization_id <> e.organization_id
       OR d.organization_id <> e.organization_id
       OR p.organization_id <> e.organization_id THEN
        RETURN QUERY SELECT FALSE, 'Organization boundary violation';
        RETURN;
    END IF;

    IF m.qubit_count > b.maximum_qubits THEN
        RETURN QUERY SELECT FALSE, 'Backend qubit capacity exceeded';
        RETURN;
    END IF;

    IF m.qubit_count > p.maximum_qubits
       OR m.qubit_count < p.minimum_qubits THEN
        RETURN QUERY SELECT FALSE, 'Qubit policy violation';
        RETURN;
    END IF;

    IF e.shots > p.maximum_shots THEN
        RETURN QUERY SELECT FALSE, 'Shot limit exceeded';
        RETURN;
    END IF;

    IF e.epochs > p.maximum_epochs THEN
        RETURN QUERY SELECT FALSE, 'Epoch limit exceeded';
        RETURN;
    END IF;

    IF m.input_dimension <> d.feature_count THEN
        RETURN QUERY SELECT FALSE, 'Dataset/model dimension mismatch';
        RETURN;
    END IF;

    IF e.execution_mode = 'quantum_hardware'
       AND NOT p.allow_hardware THEN
        RETURN QUERY SELECT FALSE, 'Hardware execution is prohibited';
        RETURN;
    END IF;

    IF e.execution_mode = 'classical_fallback'
       AND NOT p.allow_fallback THEN
        RETURN QUERY SELECT FALSE, 'Classical fallback is prohibited';
        RETURN;
    END IF;

    IF e.execution_mode <> b.execution_mode THEN
        RETURN QUERY SELECT FALSE, 'Backend execution mode mismatch';
        RETURN;
    END IF;

    IF p.require_review THEN

        SELECT COUNT(*)
        INTO approved_reviews
        FROM experiment_reviews r
        JOIN research_users u
          ON u.user_id = r.reviewer_id
        WHERE r.experiment_id = e.experiment_id
          AND r.status = 'approved'
          AND u.active = TRUE
          AND u.role IN ('reviewer', 'administrator')
          AND u.organization_id = e.organization_id;

        IF approved_reviews < 1 THEN
            RETURN QUERY SELECT FALSE, 'Approved reviewer decision required';
            RETURN;
        END IF;

    END IF;

    RETURN QUERY SELECT TRUE, 'Experiment is eligible';

END;
$$;


-- =========================================================
-- EXPERIMENT QUEUE PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE queue_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility RECORD;
BEGIN
    -- Lock the experiment to prevent concurrent queue transitions.
    PERFORM 1
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment % not found', p_experiment_id;
    END IF;

    SELECT *
    INTO eligibility
    FROM check_experiment_eligibility(p_experiment_id);

    IF NOT eligibility.eligible THEN
        RAISE EXCEPTION 'Experiment rejected: %', eligibility.reason;
    END IF;

    UPDATE experiments
    SET status = 'queued'
    WHERE experiment_id = p_experiment_id
      AND status = 'created';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Only created experiments can be queued';
    END IF;

    INSERT INTO training_runs (
        experiment_id,
        run_number,
        status
    )
    VALUES (
        p_experiment_id,
        1,
        'queued'
    );

END;
$$;


-- =========================================================
-- EXPERIMENT REPORT VIEW
-- =========================================================

CREATE OR REPLACE VIEW experiment_report AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.execution_mode,

    m.model_name,
    m.model_type,
    m.qubit_count,

    d.dataset_name,
    d.dataset_version,
    d.sample_count,

    b.backend_name,

    u.username AS experiment_owner,

    tr.run_id,
    tr.status AS run_status,
    tr.training_loss,

    em.accuracy,
    em.precision_score,
    em.recall_score,
    em.f1_score,

    e.created_at

FROM experiments e

JOIN models m
    ON m.model_id = e.model_id

JOIN datasets d
    ON d.dataset_id = e.dataset_id

JOIN quantum_backends b
    ON b.backend_id = e.backend_id

JOIN research_users u
    ON u.user_id = e.created_by

LEFT JOIN training_runs tr
    ON tr.experiment_id = e.experiment_id

LEFT JOIN evaluation_metrics em
    ON em.run_id = tr.run_id
   AND em.dataset_partition = 'testing';


-- =========================================================
-- SAMPLE ORGANIZATIONS
-- =========================================================

INSERT INTO organizations (organization_name)
VALUES
    ('Quantum Research Laboratory'),
    ('Enterprise Machine Learning Division');


-- =========================================================
-- SAMPLE USERS
-- =========================================================

INSERT INTO research_users (
    organization_id,
    username,
    role
)
VALUES
    (1, 'quantum_researcher', 'researcher'),
    (1, 'quantum_reviewer', 'reviewer'),
    (1, 'quantum_operator', 'operator'),
    (1, 'quantum_admin', 'administrator'),
    (2, 'enterprise_researcher', 'researcher');


-- =========================================================
-- SAMPLE DATASETS
-- =========================================================

INSERT INTO datasets (
    organization_id,
    dataset_name,
    dataset_version,
    feature_count,
    sample_count,
    training_samples,
    testing_samples,
    label_type,
    checksum_sha256,
    approved_for_research
)
VALUES
(
    1,
    'Synthetic Nonlinear Classification',
    '1.0',
    2,
    100,
    80,
    20,
    'binary',
    repeat('a', 64),
    TRUE
),
(
    1,
    'Unapproved Experimental Dataset',
    '1.0',
    2,
    100,
    80,
    20,
    'binary',
    repeat('b', 64),
    FALSE
);


-- =========================================================
-- SAMPLE BACKENDS
-- =========================================================

INSERT INTO quantum_backends (
    backend_name,
    execution_mode,
    provider_name,
    maximum_qubits,
    supports_shots,
    supports_noise_model
)
VALUES
(
    'Local State Vector Simulator',
    'simulator',
    'Internal',
    12,
    TRUE,
    FALSE
),
(
    'Experimental Quantum Hardware',
    'quantum_hardware',
    'External Provider',
    20,
    TRUE,
    TRUE
),
(
    'Classical Fallback Engine',
    'classical_fallback',
    'Internal',
    12,
    FALSE,
    FALSE
);


-- =========================================================
-- SAMPLE MODELS
-- =========================================================

INSERT INTO models (
    organization_id,
    model_name,
    model_type,
    description,
    input_dimension,
    qubit_count,
    parameter_count,
    created_by
)
VALUES
(
    1,
    'Hybrid Variational Classifier',
    'hybrid_feature_classifier',
    'Quantum feature extraction and classical logistic head',
    2,
    2,
    4,
    1
),
(
    1,
    'Quantum Fidelity Kernel',
    'quantum_kernel',
    'Fidelity-based quantum kernel classification',
    2,
    2,
    0,
    1
);


-- =========================================================
-- SAMPLE POLICIES
-- =========================================================

INSERT INTO execution_policies (
    organization_id,
    policy_name,
    minimum_qubits,
    maximum_qubits,
    maximum_shots,
    maximum_epochs,
    allow_hardware,
    allow_fallback,
    require_approved_dataset,
    require_review
)
VALUES
(
    1,
    'Research Simulator Policy',
    1,
    8,
    10000,
    200,
    FALSE,
    TRUE,
    TRUE,
    TRUE
),
(
    1,
    'Hardware Research Policy',
    1,
    12,
    50000,
    500,
    TRUE,
    FALSE,
    TRUE,
    TRUE
);


-- =========================================================
-- SAMPLE EXPERIMENTS
-- =========================================================

INSERT INTO experiments (
    organization_id,
    experiment_name,
    model_id,
    dataset_id,
    backend_id,
    policy_id,
    created_by,
    execution_mode,
    status,
    epochs,
    learning_rate,
    regularization,
    shots,
    random_seed
)
VALUES
(
    1,
    'Hybrid Classification Experiment',
    1,
    1,
    1,
    1,
    1,
    'simulator',
    'created',
    40,
    0.03,
    0.1,
    1000,
    42
),
(
    1,
    'Rejected Dataset Experiment',
    1,
    2,
    1,
    1,
    1,
    'simulator',
    'created',
    40,
    0.03,
    0.1,
    1000,
    43
),
(
    1,
    'Hardware Experiment',
    1,
    1,
    2,
    2,
    1,
    'quantum_hardware',
    'created',
    50,
    0.02,
    0.1,
    5000,
    44
);


-- =========================================================
-- SAMPLE REVIEW DECISIONS
-- =========================================================

INSERT INTO experiment_reviews (
    experiment_id,
    reviewer_id,
    status,
    review_comment,
    reviewed_at
)
VALUES
(
    1,
    2,
    'approved',
    'Dataset and simulation configuration reviewed',
    CURRENT_TIMESTAMP
),
(
    2,
    2,
    'approved',
    'Execution request reviewed; dataset approval remains mandatory',
    CURRENT_TIMESTAMP
),
(
    3,
    2,
    'approved',
    'Hardware execution reviewed',
    CURRENT_TIMESTAMP
);


-- =========================================================
-- ELIGIBILITY REPORT
-- =========================================================

SELECT
    e.experiment_id,
    e.experiment_name,
    eligibility.eligible,
    eligibility.reason

FROM experiments e

CROSS JOIN LATERAL
    check_experiment_eligibility(e.experiment_id) eligibility

ORDER BY e.experiment_id;


-- =========================================================
-- VALID EXPERIMENT QUEUE
-- =========================================================

CALL queue_experiment(1);


-- =========================================================
-- SAMPLE TRAINING EXECUTION
-- =========================================================

UPDATE experiments
SET
    status = 'running',
    started_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1
  AND status = 'queued';


UPDATE training_runs
SET
    status = 'running',
    started_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1
  AND run_number = 1;


INSERT INTO quantum_circuit_runs (
    run_id,
    circuit_name,
    circuit_depth,
    qubit_count,
    gate_count,
    shots,
    status,
    expectation_values,
    measurement_counts,
    execution_time_ms,
    completed_at
)
SELECT
    run_id,
    'Variational Feature Circuit',
    5,
    2,
    8,
    1000,
    'completed',
    '[0.23, -0.41]'::jsonb,
    '{"00": 430, "01": 70, "10": 80, "11": 420}'::jsonb,
    12.45,
    CURRENT_TIMESTAMP
FROM training_runs
WHERE experiment_id = 1
  AND run_number = 1;


INSERT INTO optimization_steps (
    run_id,
    epoch,
    optimizer_name,
    learning_rate,
    objective_value,
    gradient_norm,
    parameter_vector
)
SELECT
    run_id,
    1,
    'Gradient Descent with Parameter Shift',
    0.03,
    0.6921,
    0.182,
    '[0.11, -0.08, 0.21, -0.13]'::jsonb
FROM training_runs
WHERE experiment_id = 1
  AND run_number = 1;


INSERT INTO optimization_steps (
    run_id,
    epoch,
    optimizer_name,
    learning_rate,
    objective_value,
    gradient_norm,
    parameter_vector
)
SELECT
    run_id,
    2,
    'Gradient Descent with Parameter Shift',
    0.03,
    0.6742,
    0.151,
    '[0.12, -0.07, 0.22, -0.12]'::jsonb
FROM training_runs
WHERE experiment_id = 1
  AND run_number = 1;


INSERT INTO evaluation_metrics (
    run_id,
    dataset_partition,
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    true_positive,
    true_negative,
    false_positive,
    false_negative
)
SELECT
    run_id,
    'testing',
    0.85,
    0.83333333,
    0.90909091,
    0.86956522,
    10,
    7,
    2,
    1
FROM training_runs
WHERE experiment_id = 1
  AND run_number = 1;


UPDATE training_runs
SET
    status = 'completed',
    training_loss = 0.6742,
    validation_loss = 0.7012,
    completed_epochs = 40,
    completed_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1
  AND run_number = 1;


UPDATE experiments
SET
    status = 'completed',
    completed_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1
  AND status = 'running';


-- =========================================================
-- RETRIEVAL QUERIES
-- =========================================================

-- All experiments belonging to the first organization.

SELECT
    experiment_id,
    experiment_name,
    status,
    execution_mode,
    created_at
FROM experiments
WHERE organization_id = 1
ORDER BY created_at DESC;


-- Circuit execution history.

SELECT
    cr.circuit_run_id,
    cr.circuit_name,
    cr.qubit_count,
    cr.circuit_depth,
    cr.shots,
    cr.status,
    cr.execution_time_ms
FROM quantum_circuit_runs cr
JOIN training_runs tr
    ON tr.run_id = cr.run_id
WHERE tr.experiment_id = 1;


-- Classical optimization convergence.

SELECT
    epoch,
    objective_value,
    gradient_norm,
    learning_rate
FROM optimization_steps
WHERE run_id = (
    SELECT run_id
    FROM training_runs
    WHERE experiment_id = 1
    LIMIT 1
)
ORDER BY epoch;


-- =========================================================
-- AGGREGATION AND REPORTING
-- =========================================================

SELECT
    execution_mode,
    status,
    COUNT(*) AS experiment_count,
    ROUND(AVG(epochs), 2) AS average_epochs,
    ROUND(AVG(learning_rate), 6) AS average_learning_rate
FROM experiments
GROUP BY execution_mode, status
ORDER BY execution_mode, status;


SELECT
    m.model_name,
    COUNT(DISTINCT e.experiment_id) AS experiment_count,
    ROUND(AVG(em.accuracy), 4) AS average_accuracy,
    ROUND(AVG(em.f1_score), 4) AS average_f1
FROM models m
JOIN experiments e
    ON e.model_id = m.model_id
LEFT JOIN training_runs tr
    ON tr.experiment_id = e.experiment_id
LEFT JOIN evaluation_metrics em
    ON em.run_id = tr.run_id
GROUP BY m.model_id, m.model_name;


-- =========================================================
-- CIRCUIT PERFORMANCE ANALYSIS
-- =========================================================

SELECT
    circuit_name,
    qubit_count,
    AVG(circuit_depth) AS average_depth,
    AVG(gate_count) AS average_gate_count,
    AVG(execution_time_ms) AS average_execution_ms,
    SUM(shots) AS total_shots
FROM quantum_circuit_runs
WHERE status = 'completed'
GROUP BY circuit_name, qubit_count;


-- =========================================================
-- FAILURE ANALYSIS
-- =========================================================

SELECT
    experiment_id,
    experiment_name,
    status,
    failure_reason,
    created_at
FROM experiments
WHERE status = 'failed'
ORDER BY created_at DESC;


SELECT
    run_id,
    experiment_id,
    error_message
FROM training_runs
WHERE status = 'failed';


-- =========================================================
-- AUDIT REPORT
-- =========================================================

SELECT
    experiment_id,
    action,
    previous_status,
    new_status,
    details,
    created_at
FROM experiment_audit
ORDER BY created_at DESC;


-- =========================================================
-- ELIGIBILITY VALIDATION
-- =========================================================

SELECT *
FROM check_experiment_eligibility(2);


-- =========================================================
-- WORKFLOW TRANSACTION EXAMPLE
-- =========================================================

-- An invalid experiment cannot be queued.
-- The procedure raises an exception, allowing the caller
-- to roll back the transaction.

-- Example:
--
-- BEGIN;
-- CALL queue_experiment(2);
-- COMMIT;
--
-- Expected outcome:
-- Rejected because the dataset has not been approved.
--
-- The following block demonstrates explicit transaction
-- handling without leaving the main demonstration failed.

DO $$
BEGIN
    BEGIN
        CALL queue_experiment(2);

        RAISE EXCEPTION
            'Validation error: unapproved experiment was queued';

    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected rejection handled: %',
                SQLERRM;
    END;
END;
$$;


-- =========================================================
-- ORGANIZATION ISOLATION CHECK
-- =========================================================

SELECT
    u.username,
    u.role,
    COUNT(e.experiment_id) AS owned_experiments
FROM research_users u
LEFT JOIN experiments e
    ON e.created_by = u.user_id
   AND e.organization_id = u.organization_id
GROUP BY u.user_id, u.username, u.role
ORDER BY u.username;


-- =========================================================
-- FINAL EXPERIMENT REPORT
-- =========================================================

SELECT *
FROM experiment_report
ORDER BY experiment_id;


COMMIT;
