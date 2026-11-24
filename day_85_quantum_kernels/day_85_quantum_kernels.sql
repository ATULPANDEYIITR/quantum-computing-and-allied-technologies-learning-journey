-- ============================================================
-- QUANTUM KERNEL RESEARCH AND EXPERIMENT MANAGEMENT
-- PostgreSQL 15+
--
-- Models:
-- Quantum circuits
-- Feature maps
-- Datasets and observations
-- Quantum kernel matrices
-- Kernel evaluations
-- Classification experiments
-- Model training
-- Experiment validation
-- Execution records
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_research;

SET search_path TO quantum_research, public;

-- ------------------------------------------------------------
-- ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

DO $$
BEGIN
    CREATE TYPE experiment_status AS ENUM (
        'CREATED',
        'VALIDATED',
        'RUNNING',
        'COMPLETED',
        'FAILED',
        'CANCELLED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE circuit_gate AS ENUM (
        'H',
        'RX',
        'RY',
        'RZ',
        'CNOT',
        'CZ',
        'SWAP'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE kernel_method AS ENUM (
        'FIDELITY',
        'PROJECTED',
        'TRAINABLE'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE execution_backend AS ENUM (
        'STATE_VECTOR_SIMULATOR',
        'DENSITY_MATRIX_SIMULATOR',
        'QUANTUM_HARDWARE'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    CREATE TYPE evaluation_status AS ENUM (
        'PENDING',
        'COMPUTED',
        'FAILED'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ------------------------------------------------------------
-- RESEARCH ORGANIZATIONS AND USERS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS research_organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(180) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES research_organizations(organization_id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- QUANTUM CIRCUITS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name VARCHAR(150) NOT NULL,
    qubit_count SMALLINT NOT NULL
        CHECK (qubit_count BETWEEN 1 AND 1000),
    feature_dimension SMALLINT NOT NULL
        CHECK (feature_dimension > 0),
    feature_map_type VARCHAR(80) NOT NULL,
    rotation_scale DOUBLE PRECISION NOT NULL DEFAULT 2.0
        CHECK (
            rotation_scale > 0
            AND rotation_scale < 'Infinity'::DOUBLE PRECISION
        ),
    entanglement_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    circuit_depth INTEGER NOT NULL
        CHECK (circuit_depth >= 0),
    gate_count INTEGER NOT NULL
        CHECK (gate_count >= 0),
    circuit_description TEXT,
    created_by BIGINT REFERENCES researchers(researcher_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (circuit_name, feature_map_type)
);

CREATE TABLE IF NOT EXISTS circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL CHECK (sequence_number > 0),
    gate_type circuit_gate NOT NULL,
    target_qubit SMALLINT NOT NULL CHECK (target_qubit >= 0),
    control_qubit SMALLINT,
    rotation_angle DOUBLE PRECISION,
    CHECK (
        rotation_angle IS NULL
        OR rotation_angle > '-Infinity'::DOUBLE PRECISION
        AND rotation_angle < 'Infinity'::DOUBLE PRECISION
    ),
    CHECK (
        control_qubit IS NULL
        OR control_qubit <> target_qubit
    ),
    UNIQUE (circuit_id, sequence_number)
);

-- ------------------------------------------------------------
-- DATASETS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_name VARCHAR(180) NOT NULL UNIQUE,
    feature_dimension SMALLINT NOT NULL
        CHECK (feature_dimension > 0),
    sample_count INTEGER NOT NULL DEFAULT 0
        CHECK (sample_count >= 0),
    description TEXT,
    data_version VARCHAR(50) NOT NULL,
    created_by BIGINT REFERENCES researchers(researcher_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dataset_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id) ON DELETE CASCADE,
    external_sample_key VARCHAR(150) NOT NULL,
    features DOUBLE PRECISION[] NOT NULL,
    class_label SMALLINT NOT NULL CHECK (class_label IN (-1, 1)),
    partition_name VARCHAR(20) NOT NULL
        CHECK (partition_name IN ('TRAIN', 'VALIDATION', 'TEST')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (dataset_id, external_sample_key)
);

CREATE INDEX IF NOT EXISTS idx_observations_partition
ON dataset_observations(dataset_id, partition_name);

-- ------------------------------------------------------------
-- KERNEL CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS kernel_configurations (
    kernel_config_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    configuration_name VARCHAR(150) NOT NULL UNIQUE,
    kernel_type kernel_method NOT NULL,
    kernel_formula TEXT NOT NULL,
    measurement_shots INTEGER
        CHECK (measurement_shots IS NULL OR measurement_shots > 0),
    regularization DOUBLE PRECISION NOT NULL DEFAULT 0.1
        CHECK (
            regularization > 0
            AND regularization < 'Infinity'::DOUBLE PRECISION
        ),
    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_name VARCHAR(180) NOT NULL UNIQUE,
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id),
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    kernel_config_id BIGINT NOT NULL
        REFERENCES kernel_configurations(kernel_config_id),
    researcher_id BIGINT NOT NULL REFERENCES researchers(researcher_id),
    backend execution_backend NOT NULL,
    status experiment_status NOT NULL DEFAULT 'CREATED',
    random_seed INTEGER NOT NULL DEFAULT 42,
    training_sample_count INTEGER NOT NULL DEFAULT 0
        CHECK (training_sample_count >= 0),
    testing_sample_count INTEGER NOT NULL DEFAULT 0
        CHECK (testing_sample_count >= 0),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),
    CHECK (
        completed_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE INDEX IF NOT EXISTS idx_experiment_status
ON experiments(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_experiment_researcher
ON experiments(researcher_id, created_at DESC);

-- ------------------------------------------------------------
-- KERNEL EVALUATIONS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS kernel_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    first_observation_id BIGINT NOT NULL
        REFERENCES dataset_observations(observation_id),
    second_observation_id BIGINT NOT NULL
        REFERENCES dataset_observations(observation_id),
    kernel_value DOUBLE PRECISION,
    evaluation_status evaluation_status NOT NULL DEFAULT 'PENDING',
    execution_time_ms NUMERIC(14, 4),
    error_message TEXT,
    computed_at TIMESTAMPTZ,
    CHECK (
        kernel_value IS NULL
        OR kernel_value >= 0
        AND kernel_value <= 1
        AND kernel_value < 'Infinity'::DOUBLE PRECISION
    ),
    CHECK (
        execution_time_ms IS NULL
        OR execution_time_ms >= 0
    ),
    CHECK (
        first_observation_id <> second_observation_id
        OR kernel_value = 1.0
        OR evaluation_status <> 'COMPUTED'
    ),
    CHECK (
        (evaluation_status = 'COMPUTED'
            AND kernel_value IS NOT NULL
            AND computed_at IS NOT NULL)
        OR evaluation_status <> 'COMPUTED'
    ),
    UNIQUE (
        experiment_id,
        first_observation_id,
        second_observation_id
    )
);

CREATE INDEX IF NOT EXISTS idx_kernel_evaluation_status
ON kernel_evaluations(experiment_id, evaluation_status);

-- ------------------------------------------------------------
-- KERNEL MATRIX METADATA
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS kernel_matrices (
    matrix_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    matrix_dimension INTEGER NOT NULL CHECK (matrix_dimension > 0),
    is_symmetric BOOLEAN NOT NULL DEFAULT FALSE,
    diagonal_validated BOOLEAN NOT NULL DEFAULT FALSE,
    positive_semidefinite BOOLEAN,
    minimum_eigenvalue DOUBLE PRECISION,
    matrix_checksum VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        minimum_eigenvalue IS NULL
        OR minimum_eigenvalue > '-Infinity'::DOUBLE PRECISION
        AND minimum_eigenvalue < 'Infinity'::DOUBLE PRECISION
    )
);

-- ------------------------------------------------------------
-- MODEL RESULTS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS model_results (
    model_result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    algorithm VARCHAR(100) NOT NULL,
    regularization DOUBLE PRECISION NOT NULL
        CHECK (regularization > 0),
    accuracy NUMERIC(8, 6)
        CHECK (accuracy BETWEEN 0 AND 1),
    precision_score NUMERIC(8, 6)
        CHECK (precision_score BETWEEN 0 AND 1),
    recall_score NUMERIC(8, 6)
        CHECK (recall_score BETWEEN 0 AND 1),
    f1_score NUMERIC(8, 6)
        CHECK (f1_score BETWEEN 0 AND 1),
    true_positive INTEGER NOT NULL DEFAULT 0 CHECK (true_positive >= 0),
    true_negative INTEGER NOT NULL DEFAULT 0 CHECK (true_negative >= 0),
    false_positive INTEGER NOT NULL DEFAULT 0 CHECK (false_positive >= 0),
    false_negative INTEGER NOT NULL DEFAULT 0 CHECK (false_negative >= 0),
    training_time_ms NUMERIC(14, 4),
    inference_time_ms NUMERIC(14, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- EXPERIMENT AUDIT LOG
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    previous_status experiment_status,
    new_status experiment_status NOT NULL,
    event_description TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_experiment_time
ON experiment_audit(experiment_id, event_time DESC);

-- ------------------------------------------------------------
-- OBSERVATION VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_observation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_dimension INTEGER;
BEGIN
    SELECT feature_dimension
    INTO expected_dimension
    FROM datasets
    WHERE dataset_id = NEW.dataset_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dataset % does not exist', NEW.dataset_id;
    END IF;

    IF array_length(NEW.features, 1) IS DISTINCT FROM expected_dimension THEN
        RAISE EXCEPTION
            'Feature dimension mismatch: expected %, received %',
            expected_dimension,
            array_length(NEW.features, 1);
    END IF;

    IF array_position(NEW.features, NULL) IS NOT NULL THEN
        RAISE EXCEPTION 'Feature arrays cannot contain NULL values';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM unnest(NEW.features) AS feature
        WHERE feature <= '-Infinity'::DOUBLE PRECISION
           OR feature >= 'Infinity'::DOUBLE PRECISION
    ) THEN
        RAISE EXCEPTION 'Features must be finite numbers';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_observation
ON dataset_observations;

CREATE TRIGGER trg_validate_observation
BEFORE INSERT OR UPDATE
ON dataset_observations
FOR EACH ROW
EXECUTE FUNCTION validate_observation();

-- ------------------------------------------------------------
-- MAINTAIN DATASET SAMPLE COUNTS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION maintain_sample_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE datasets
        SET sample_count = sample_count + 1
        WHERE dataset_id = NEW.dataset_id;

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE datasets
        SET sample_count = sample_count - 1
        WHERE dataset_id = OLD.dataset_id;

        RETURN OLD;

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.dataset_id <> NEW.dataset_id THEN
            UPDATE datasets
            SET sample_count = sample_count - 1
            WHERE dataset_id = OLD.dataset_id;

            UPDATE datasets
            SET sample_count = sample_count + 1
            WHERE dataset_id = NEW.dataset_id;
        END IF;

        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_sample_count
ON dataset_observations;

CREATE TRIGGER trg_sample_count
AFTER INSERT OR UPDATE OR DELETE
ON dataset_observations
FOR EACH ROW
EXECUTE FUNCTION maintain_sample_count();

-- ------------------------------------------------------------
-- EXPERIMENT STATE TRANSITION VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        RAISE EXCEPTION
            'Terminal experiment status % cannot be changed',
            OLD.status;
    END IF;

    IF NEW.status = 'RUNNING'
       AND OLD.status NOT IN ('CREATED', 'VALIDATED') THEN
        RAISE EXCEPTION 'Invalid transition to RUNNING';
    END IF;

    IF NEW.status = 'COMPLETED'
       AND OLD.status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Experiment must be RUNNING before completion';
    END IF;

    IF NEW.status = 'VALIDATED'
       AND OLD.status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Only CREATED experiments can be validated';
    END IF;

    IF NEW.status = 'RUNNING' THEN
        NEW.started_at = COALESCE(NEW.started_at, NOW());
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = COALESCE(NEW.completed_at, NOW());
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_experiment_transition
ON experiments;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status
ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_transition();

-- ------------------------------------------------------------
-- EXPERIMENT AUDIT CAPTURE
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION record_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO experiment_audit (
            experiment_id,
            previous_status,
            new_status,
            event_description
        )
        VALUES (
            NEW.experiment_id,
            OLD.status,
            NEW.status,
            'Experiment state transition'
        );
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_experiment_audit
ON experiments;

CREATE TRIGGER trg_experiment_audit
AFTER UPDATE OF status
ON experiments
FOR EACH ROW
EXECUTE FUNCTION record_experiment_transition();

-- ------------------------------------------------------------
-- VALIDATE KERNEL EVALUATION RESULTS
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_kernel_evaluation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    first_dataset BIGINT;
    second_dataset BIGINT;
BEGIN
    SELECT dataset_id
    INTO first_dataset
    FROM dataset_observations
    WHERE observation_id = NEW.first_observation_id;

    SELECT dataset_id
    INTO second_dataset
    FROM dataset_observations
    WHERE observation_id = NEW.second_observation_id;

    IF first_dataset IS NULL OR second_dataset IS NULL THEN
        RAISE EXCEPTION 'Kernel observations must exist';
    END IF;

    IF first_dataset <> second_dataset THEN
        RAISE EXCEPTION
            'Kernel evaluations must use observations from one dataset';
    END IF;

    IF NEW.evaluation_status = 'COMPUTED' THEN
        IF NEW.kernel_value IS NULL THEN
            RAISE EXCEPTION 'Computed kernel requires a value';
        END IF;

        IF NEW.computed_at IS NULL THEN
            NEW.computed_at = NOW();
        END IF;
    END IF;

    IF NEW.evaluation_status = 'FAILED'
       AND NEW.error_message IS NULL THEN
        RAISE EXCEPTION 'Failed evaluations require an error message';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_validate_kernel_evaluation
ON kernel_evaluations;

CREATE TRIGGER trg_validate_kernel_evaluation
BEFORE INSERT OR UPDATE
ON kernel_evaluations
FOR EACH ROW
EXECUTE FUNCTION validate_kernel_evaluation();

-- ------------------------------------------------------------
-- SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO research_organizations (organization_name)
VALUES ('Quantum Computing Research Laboratory')
ON CONFLICT (organization_name) DO NOTHING;

INSERT INTO researchers (
    organization_id,
    full_name,
    email
)
SELECT
    organization_id,
    'Research Administrator',
    'research.admin@example.org'
FROM research_organizations
WHERE organization_name =
    'Quantum Computing Research Laboratory'
ON CONFLICT (email) DO NOTHING;

INSERT INTO circuits (
    circuit_name,
    qubit_count,
    feature_dimension,
    feature_map_type,
    rotation_scale,
    entanglement_enabled,
    circuit_depth,
    gate_count,
    circuit_description,
    created_by
)
SELECT
    'Two Qubit Fidelity Feature Map',
    2,
    2,
    'H-RZ-RX-CZ',
    2.0,
    TRUE,
    5,
    5,
    'Hadamard, data-dependent rotations and CZ entanglement.',
    researcher_id
FROM researchers
WHERE email = 'research.admin@example.org'
ON CONFLICT (circuit_name, feature_map_type) DO NOTHING;

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit
)
SELECT circuit_id, 1, 'H', 0
FROM circuits
WHERE circuit_name = 'Two Qubit Fidelity Feature Map'
ON CONFLICT (circuit_id, sequence_number) DO NOTHING;

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit
)
SELECT circuit_id, 2, 'H', 1
FROM circuits
WHERE circuit_name = 'Two Qubit Fidelity Feature Map'
ON CONFLICT (circuit_id, sequence_number) DO NOTHING;

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit,
    rotation_angle
)
SELECT circuit_id, 3, 'RZ', 0, 2.0
FROM circuits
WHERE circuit_name = 'Two Qubit Fidelity Feature Map'
ON CONFLICT (circuit_id, sequence_number) DO NOTHING;

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit,
    rotation_angle
)
SELECT circuit_id, 4, 'RX', 1, 2.0
FROM circuits
WHERE circuit_name = 'Two Qubit Fidelity Feature Map'
ON CONFLICT (circuit_id, sequence_number) DO NOTHING;

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate_type,
    target_qubit,
    control_qubit
)
SELECT circuit_id, 5, 'CZ', 1, 0
FROM circuits
WHERE circuit_name = 'Two Qubit Fidelity Feature Map'
ON CONFLICT (circuit_id, sequence_number) DO NOTHING;

INSERT INTO datasets (
    dataset_name,
    feature_dimension,
    description,
    data_version,
    created_by
)
SELECT
    'Nonlinear Quantum Kernel Benchmark',
    2,
    'Synthetic binary classification dataset.',
    '1.0',
    researcher_id
FROM researchers
WHERE email = 'research.admin@example.org'
ON CONFLICT (dataset_name) DO NOTHING;

-- Generate 32 reproducible observations.
-- A nonlinear decision boundary is used.
INSERT INTO dataset_observations (
    dataset_id,
    external_sample_key,
    features,
    class_label,
    partition_name
)
SELECT
    d.dataset_id,
    'SAMPLE-' || lpad(i::TEXT, 3, '0'),
    ARRAY[
        (-1.2 + 2.4 * ((i - 1) % 8)::DOUBLE PRECISION / 7.0),
        (-1.2 + 2.4 * ((i - 1) / 8)::DOUBLE PRECISION / 3.0)
    ],
    CASE
        WHEN
            sin(2.0 * (-1.2 + 2.4 * ((i - 1) % 8)::DOUBLE PRECISION / 7.0))
            *
            cos(2.0 * (-1.2 + 2.4 * ((i - 1) / 8)::DOUBLE PRECISION / 3.0))
            >= 0
        THEN 1
        ELSE -1
    END,
    CASE
        WHEN i <= 24 THEN 'TRAIN'
        ELSE 'TEST'
    END
FROM datasets d
CROSS JOIN generate_series(1, 32) AS i
WHERE d.dataset_name = 'Nonlinear Quantum Kernel Benchmark'
ON CONFLICT (dataset_id, external_sample_key) DO NOTHING;

INSERT INTO kernel_configurations (
    configuration_name,
    kernel_type,
    kernel_formula,
    regularization,
    configuration
)
VALUES (
    'Fidelity Ridge Baseline',
    'FIDELITY',
    '|<phi(x)|phi(z)>|^2',
    0.15,
    '{"classifier":"kernel_ridge","normalization":"state_vector"}'
)
ON CONFLICT (configuration_name) DO NOTHING;

INSERT INTO experiments (
    experiment_name,
    circuit_id,
    dataset_id,
    kernel_config_id,
    researcher_id,
    backend,
    random_seed,
    training_sample_count,
    testing_sample_count
)
SELECT
    'Two Qubit Nonlinear Classification',
    c.circuit_id,
    d.dataset_id,
    k.kernel_config_id,
    r.researcher_id,
    'STATE_VECTOR_SIMULATOR',
    42,
    24,
    8
FROM circuits c
CROSS JOIN datasets d
CROSS JOIN kernel_configurations k
CROSS JOIN researchers r
WHERE c.circuit_name = 'Two Qubit Fidelity Feature Map'
AND d.dataset_name = 'Nonlinear Quantum Kernel Benchmark'
AND k.configuration_name = 'Fidelity Ridge Baseline'
AND r.email = 'research.admin@example.org'
ON CONFLICT (experiment_name) DO NOTHING;

-- ------------------------------------------------------------
-- COMPUTE ELIGIBILITY
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_experiment_eligibility(
    requested_experiment BIGINT
)
RETURNS TABLE (
    experiment_id BIGINT,
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    exp RECORD;
    training_count INTEGER;
    testing_count INTEGER;
    dimension_valid BOOLEAN;
    class_count INTEGER;
BEGIN
    SELECT
        e.*,
        c.feature_dimension AS circuit_dimension,
        d.feature_dimension AS dataset_dimension
    INTO exp
    FROM experiments e
    JOIN circuits c ON c.circuit_id = e.circuit_id
    JOIN datasets d ON d.dataset_id = e.dataset_id
    WHERE e.experiment_id = requested_experiment;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT requested_experiment, FALSE, 'Experiment does not exist';
        RETURN;
    END IF;

    SELECT COUNT(*)::INTEGER
    INTO training_count
    FROM dataset_observations
    WHERE dataset_id = exp.dataset_id
    AND partition_name = 'TRAIN';

    SELECT COUNT(*)::INTEGER
    INTO testing_count
    FROM dataset_observations
    WHERE dataset_id = exp.dataset_id
    AND partition_name = 'TEST';

    SELECT COUNT(DISTINCT class_label)::INTEGER
    INTO class_count
    FROM dataset_observations
    WHERE dataset_id = exp.dataset_id
    AND partition_name = 'TRAIN';

    dimension_valid :=
        exp.circuit_dimension = exp.dataset_dimension;

    IF NOT dimension_valid THEN
        RETURN QUERY
        SELECT requested_experiment, FALSE,
            'Circuit and dataset dimensions differ';
        RETURN;
    END IF;

    IF training_count < 2 THEN
        RETURN QUERY
        SELECT requested_experiment, FALSE,
            'Insufficient training observations';
        RETURN;
    END IF;

    IF testing_count < 1 THEN
        RETURN QUERY
        SELECT requested_experiment, FALSE,
            'Testing observations are missing';
        RETURN;
    END IF;

    IF class_count < 2 THEN
        RETURN QUERY
        SELECT requested_experiment, FALSE,
            'Training data must contain both classes';
        RETURN;
    END IF;

    RETURN QUERY
    SELECT requested_experiment, TRUE,
        'Experiment satisfies structural eligibility rules';
END;
$$;

-- ------------------------------------------------------------
-- WORKFLOW PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_experiment(
    requested_experiment BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility RECORD;
BEGIN
    SELECT *
    INTO eligibility
    FROM get_experiment_eligibility(requested_experiment);

    IF NOT eligibility.eligible THEN
        RAISE EXCEPTION
            'Experiment cannot start: %',
            eligibility.reason;
    END IF;

    UPDATE experiments
    SET status = 'VALIDATED'
    WHERE experiment_id = requested_experiment
    AND status = 'CREATED';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment is not in CREATED state';
    END IF;

    UPDATE experiments
    SET status = 'RUNNING'
    WHERE experiment_id = requested_experiment;
END;
$$;

-- ------------------------------------------------------------
-- KERNEL EVALUATION RETRIEVAL
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_experiment_overview AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    e.backend,
    c.circuit_name,
    c.qubit_count,
    c.feature_dimension,
    d.dataset_name,
    d.sample_count,
    k.configuration_name,
    k.kernel_type,
    k.regularization,
    r.full_name AS researcher
FROM experiments e
JOIN circuits c ON c.circuit_id = e.circuit_id
JOIN datasets d ON d.dataset_id = e.dataset_id
JOIN kernel_configurations k
    ON k.kernel_config_id = e.kernel_config_id
JOIN researchers r ON r.researcher_id = e.researcher_id;

CREATE OR REPLACE VIEW v_kernel_evaluation_summary AS
SELECT
    experiment_id,
    COUNT(*) AS total_evaluations,
    COUNT(*) FILTER (
        WHERE evaluation_status = 'COMPUTED'
    ) AS successful_evaluations,
    COUNT(*) FILTER (
        WHERE evaluation_status = 'FAILED'
    ) AS failed_evaluations,
    AVG(kernel_value) FILTER (
        WHERE evaluation_status = 'COMPUTED'
    ) AS mean_kernel_value,
    AVG(execution_time_ms) AS mean_execution_ms
FROM kernel_evaluations
GROUP BY experiment_id;

CREATE OR REPLACE VIEW v_classification_performance AS
SELECT
    e.experiment_name,
    e.status,
    m.algorithm,
    m.accuracy,
    m.precision_score,
    m.recall_score,
    m.f1_score,
    m.training_time_ms,
    m.inference_time_ms
FROM experiments e
JOIN model_results m
    ON m.experiment_id = e.experiment_id;

-- ------------------------------------------------------------
-- REPORTING QUERIES
-- ------------------------------------------------------------

-- Experiment configuration and status.
SELECT *
FROM v_experiment_overview
ORDER BY experiment_id;

-- Structural eligibility.
SELECT *
FROM get_experiment_eligibility(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_name =
            'Two Qubit Nonlinear Classification'
    )
);

-- Dataset partition and class distribution.
SELECT
    partition_name,
    class_label,
    COUNT(*) AS observations
FROM dataset_observations
GROUP BY partition_name, class_label
ORDER BY partition_name, class_label;

-- Circuit complexity.
SELECT
    c.circuit_name,
    c.qubit_count,
    c.circuit_depth,
    c.gate_count,
    COUNT(g.gate_id) AS registered_gates
FROM circuits c
LEFT JOIN circuit_gates g
    ON g.circuit_id = c.circuit_id
GROUP BY
    c.circuit_id,
    c.circuit_name,
    c.qubit_count,
    c.circuit_depth,
    c.gate_count;

-- Experiment resource utilization.
SELECT
    backend,
    status,
    COUNT(*) AS experiment_count,
    AVG(training_sample_count) AS mean_training_samples,
    AVG(testing_sample_count) AS mean_testing_samples
FROM experiments
GROUP BY backend, status;

-- Audit history.
SELECT
    e.experiment_name,
    a.previous_status,
    a.new_status,
    a.event_description,
    a.event_time
FROM experiment_audit a
JOIN experiments e
    ON e.experiment_id = a.experiment_id
ORDER BY a.event_time DESC;

-- ------------------------------------------------------------
-- TRANSACTIONAL EXPERIMENT START
-- ------------------------------------------------------------

DO $$
DECLARE
    target_experiment BIGINT;
BEGIN
    SELECT experiment_id
    INTO target_experiment
    FROM experiments
    WHERE experiment_name =
        'Two Qubit Nonlinear Classification';

    IF target_experiment IS NOT NULL THEN
        IF EXISTS (
            SELECT 1
            FROM experiments
            WHERE experiment_id = target_experiment
            AND status = 'CREATED'
        ) THEN
            CALL start_experiment(target_experiment);
        END IF;
    END IF;
END;
$$;

COMMIT;

-- ------------------------------------------------------------
-- OPERATIONAL NOTES
-- ------------------------------------------------------------

-- The database stores experiment metadata and kernel evaluations.
-- It does not execute quantum gates or calculate eigenvalues.
--
-- Positive-semidefinite status must be established by the
-- numerical computation service and recorded in kernel_matrices.
--
-- For a fidelity kernel, K(x,x) should equal 1 for normalized
-- quantum states.
--
-- A symmetric matrix is not necessarily positive semidefinite.
--
-- Production deployments should use:
--   - restricted database roles
--   - encrypted connections
--   - dataset access controls
--   - immutable audit retention
--   - transaction isolation appropriate to concurrent workers
--   - numerical validation in the computation service
--
-- The sample dataset and experiment are synthetic.
