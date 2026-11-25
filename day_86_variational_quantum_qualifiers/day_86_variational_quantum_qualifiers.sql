-- ============================================================
-- VARIATIONAL QUANTUM CLASSIFIER
-- PostgreSQL 15+
--
-- Relational experiment management and quantum classification
-- workflow.
--
-- Includes:
--   Experiments
--   Quantum circuit configurations
--   Training datasets
--   Classification samples
--   Variational parameters
--   Training epochs
--   Predictions
--   Evaluation metrics
--   Model lifecycle
--   Validation functions
--   Triggers
--   Views
--   Transactional training updates
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_ml;

SET search_path TO quantum_ml, public;

-- ------------------------------------------------------------
-- 1. ENUMERATED DOMAIN TYPES
-- ------------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'TRAINING',
    'TRAINED',
    'EVALUATED',
    'FAILED',
    'ARCHIVED'
);

CREATE TYPE sample_split AS ENUM (
    'TRAIN',
    'VALIDATION',
    'TEST'
);

CREATE TYPE classification_label AS ENUM (
    'NEGATIVE',
    'POSITIVE'
);

CREATE TYPE optimization_status AS ENUM (
    'RUNNING',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE prediction_status AS ENUM (
    'PENDING',
    'COMPLETED',
    'FAILED'
);

-- ------------------------------------------------------------
-- 2. EXPERIMENTS
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    qubit_count INTEGER NOT NULL DEFAULT 2
        CHECK (qubit_count > 0 AND qubit_count <= 30),

    circuit_depth INTEGER NOT NULL
        CHECK (circuit_depth > 0),

    feature_count INTEGER NOT NULL
        CHECK (feature_count > 0),

    trainable_parameter_count INTEGER NOT NULL
        CHECK (trainable_parameter_count > 0),

    learning_rate NUMERIC(12, 8) NOT NULL
        CHECK (learning_rate > 0 AND learning_rate <= 1),

    epoch_limit INTEGER NOT NULL
        CHECK (epoch_limit BETWEEN 1 AND 100000),

    random_seed INTEGER NOT NULL DEFAULT 42,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    CHECK (
        completed_at IS NULL OR started_at IS NOT NULL
    )
);

CREATE INDEX idx_experiments_status
ON experiments(status, created_at DESC);

-- ------------------------------------------------------------
-- 3. QUANTUM CIRCUIT CONFIGURATION
-- ------------------------------------------------------------

CREATE TABLE circuit_layers (
    layer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    layer_number INTEGER NOT NULL CHECK (layer_number >= 0),

    layer_type VARCHAR(30) NOT NULL
        CHECK (
            layer_type IN (
                'FEATURE_MAP',
                'ENTANGLING',
                'VARIATIONAL',
                'MEASUREMENT'
            )
        ),

    gate_configuration JSONB NOT NULL DEFAULT '{}'::JSONB,

    UNIQUE (experiment_id, layer_number)
);

CREATE INDEX idx_circuit_layers_experiment
ON circuit_layers(experiment_id, layer_number);

-- ------------------------------------------------------------
-- 4. DATASETS
-- ------------------------------------------------------------

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_name VARCHAR(150) NOT NULL UNIQUE,

    feature_count INTEGER NOT NULL CHECK (feature_count > 0),

    total_samples INTEGER NOT NULL DEFAULT 0
        CHECK (total_samples >= 0),

    source_description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 5. CLASSIFICATION SAMPLES
-- ------------------------------------------------------------

CREATE TABLE classification_samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,

    sample_reference VARCHAR(100) NOT NULL,

    feature_vector JSONB NOT NULL,

    label classification_label NOT NULL,

    data_split sample_split NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(dataset_id, sample_reference),

    CHECK (
        jsonb_typeof(feature_vector) = 'array'
    )
);

CREATE INDEX idx_samples_dataset_split
ON classification_samples(dataset_id, data_split);

CREATE INDEX idx_samples_dataset_label
ON classification_samples(dataset_id, label);

CREATE INDEX idx_samples_features
ON classification_samples USING GIN(feature_vector);

-- ------------------------------------------------------------
-- 6. EXPERIMENT DATASET ASSOCIATION
-- ------------------------------------------------------------

CREATE TABLE experiment_datasets (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE RESTRICT,

    training_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (experiment_id, dataset_id)
);

-- ------------------------------------------------------------
-- 7. VARIATIONAL PARAMETERS
-- ------------------------------------------------------------

CREATE TABLE variational_parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    parameter_index INTEGER NOT NULL
        CHECK (parameter_index >= 0),

    parameter_value DOUBLE PRECISION NOT NULL
        CHECK (
            parameter_value > '-Infinity'::DOUBLE PRECISION
            AND parameter_value < 'Infinity'::DOUBLE PRECISION
        ),

    parameter_group VARCHAR(50) NOT NULL DEFAULT 'ANSATZ',

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, parameter_index)
);

CREATE INDEX idx_parameters_experiment
ON variational_parameters(experiment_id, parameter_index);

-- ------------------------------------------------------------
-- 8. OPTIMIZATION RUNS
-- ------------------------------------------------------------

CREATE TABLE optimization_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    run_number INTEGER NOT NULL CHECK (run_number > 0),

    status optimization_status NOT NULL DEFAULT 'RUNNING',

    epochs_completed INTEGER NOT NULL DEFAULT 0
        CHECK (epochs_completed >= 0),

    initial_loss DOUBLE PRECISION
        CHECK (initial_loss IS NULL OR initial_loss >= 0),

    final_loss DOUBLE PRECISION
        CHECK (final_loss IS NULL OR final_loss >= 0),

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    UNIQUE(experiment_id, run_number),

    CHECK (
        completed_at IS NULL OR
        completed_at >= started_at
    )
);

CREATE INDEX idx_runs_experiment_status
ON optimization_runs(experiment_id, status);

-- ------------------------------------------------------------
-- 9. EPOCH HISTORY
-- ------------------------------------------------------------

CREATE TABLE training_epochs (
    epoch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    epoch_number INTEGER NOT NULL CHECK (epoch_number >= 0),

    training_loss DOUBLE PRECISION NOT NULL
        CHECK (
            training_loss >= 0
            AND training_loss < 'Infinity'::DOUBLE PRECISION
        ),

    gradient_norm DOUBLE PRECISION
        CHECK (
            gradient_norm IS NULL OR
            (
                gradient_norm >= 0
                AND gradient_norm < 'Infinity'::DOUBLE PRECISION
            )
        ),

    learning_rate DOUBLE PRECISION NOT NULL
        CHECK (learning_rate > 0 AND learning_rate <= 1),

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(run_id, epoch_number)
);

CREATE INDEX idx_training_epochs_run
ON training_epochs(run_id, epoch_number);

-- ------------------------------------------------------------
-- 10. PREDICTIONS
-- ------------------------------------------------------------

CREATE TABLE predictions (
    prediction_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    sample_id BIGINT NOT NULL
        REFERENCES classification_samples(sample_id)
        ON DELETE RESTRICT,

    run_id BIGINT
        REFERENCES optimization_runs(run_id)
        ON DELETE SET NULL,

    predicted_probability DOUBLE PRECISION
        CHECK (
            predicted_probability IS NULL OR
            predicted_probability BETWEEN 0 AND 1
        ),

    predicted_label classification_label,

    status prediction_status NOT NULL DEFAULT 'PENDING',

    inference_time_ms NUMERIC(14, 6)
        CHECK (
            inference_time_ms IS NULL OR inference_time_ms >= 0
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        status <> 'COMPLETED'
        OR (
            predicted_probability IS NOT NULL
            AND predicted_label IS NOT NULL
        )
    )
);

CREATE INDEX idx_predictions_experiment
ON predictions(experiment_id, created_at DESC);

CREATE INDEX idx_predictions_sample
ON predictions(sample_id);

-- ------------------------------------------------------------
-- 11. EVALUATION METRICS
-- ------------------------------------------------------------

CREATE TABLE evaluation_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    run_id BIGINT NOT NULL
        REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    evaluated_split sample_split NOT NULL,

    accuracy DOUBLE PRECISION NOT NULL
        CHECK (accuracy BETWEEN 0 AND 1),

    precision_score DOUBLE PRECISION NOT NULL
        CHECK (precision_score BETWEEN 0 AND 1),

    recall_score DOUBLE PRECISION NOT NULL
        CHECK (recall_score BETWEEN 0 AND 1),

    f1_score DOUBLE PRECISION NOT NULL
        CHECK (f1_score BETWEEN 0 AND 1),

    cross_entropy_loss DOUBLE PRECISION NOT NULL
        CHECK (cross_entropy_loss >= 0),

    true_positive INTEGER NOT NULL CHECK (true_positive >= 0),

    false_positive INTEGER NOT NULL CHECK (false_positive >= 0),

    true_negative INTEGER NOT NULL CHECK (true_negative >= 0),

    false_negative INTEGER NOT NULL CHECK (false_negative >= 0),

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(run_id, evaluated_split)
);

CREATE INDEX idx_metrics_experiment
ON evaluation_metrics(experiment_id, evaluated_at DESC);

-- ------------------------------------------------------------
-- 12. PARAMETER VALIDATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_parameter_configuration(
    p_experiment_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
    actual_count INTEGER;
    minimum_index INTEGER;
    maximum_index INTEGER;
BEGIN
    SELECT trainable_parameter_count
    INTO expected_count
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment % does not exist',
            p_experiment_id;
    END IF;

    SELECT COUNT(*), MIN(parameter_index), MAX(parameter_index)
    INTO actual_count, minimum_index, maximum_index
    FROM variational_parameters
    WHERE experiment_id = p_experiment_id;

    IF actual_count <> expected_count THEN
        RETURN FALSE;
    END IF;

    IF minimum_index <> 0 OR maximum_index <> expected_count - 1 THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$;

-- ------------------------------------------------------------
-- 13. DATASET VALIDATION FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_dataset(
    p_experiment_id BIGINT,
    p_dataset_id BIGINT
)
RETURNS TABLE (
    valid BOOLEAN,
    training_count BIGINT,
    positive_count BIGINT,
    negative_count BIGINT,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    expected_features INTEGER;
    actual_features INTEGER;
BEGIN
    SELECT feature_count
    INTO expected_features
    FROM experiments
    WHERE experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown experiment.';
    END IF;

    SELECT feature_count
    INTO actual_features
    FROM datasets
    WHERE dataset_id = p_dataset_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unknown dataset.';
    END IF;

    SELECT
        COUNT(*) FILTER (WHERE data_split = 'TRAIN'),
        COUNT(*) FILTER (
            WHERE data_split = 'TRAIN'
            AND label = 'POSITIVE'
        ),
        COUNT(*) FILTER (
            WHERE data_split = 'TRAIN'
            AND label = 'NEGATIVE'
        )
    INTO training_count, positive_count, negative_count
    FROM classification_samples
    WHERE dataset_id = p_dataset_id;

    IF expected_features <> actual_features THEN
        valid := FALSE;
        reason := 'Feature dimension mismatch';
    ELSIF training_count < 2 THEN
        valid := FALSE;
        reason := 'Insufficient training samples';
    ELSIF positive_count = 0 OR negative_count = 0 THEN
        valid := FALSE;
        reason := 'Both training classes are required';
    ELSE
        valid := TRUE;
        reason := 'Dataset validation passed';
    END IF;

    RETURN NEXT;
END;
$$;

-- ------------------------------------------------------------
-- 14. PARAMETER UPDATE TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_parameter_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_parameter_timestamp
BEFORE UPDATE ON variational_parameters
FOR EACH ROW
EXECUTE FUNCTION update_parameter_timestamp();

-- ------------------------------------------------------------
-- 15. SAMPLE FEATURE VALIDATION TRIGGER
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_sample_features()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
    actual_count INTEGER;
    item JSONB;
BEGIN
    SELECT feature_count
    INTO expected_count
    FROM datasets
    WHERE dataset_id = NEW.dataset_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Dataset does not exist.';
    END IF;

    IF jsonb_typeof(NEW.feature_vector) <> 'array' THEN
        RAISE EXCEPTION 'Feature vector must be a JSON array.';
    END IF;

    actual_count := jsonb_array_length(NEW.feature_vector);

    IF actual_count <> expected_count THEN
        RAISE EXCEPTION
            'Expected % features, received %',
            expected_count, actual_count;
    END IF;

    FOR item IN
        SELECT value
        FROM jsonb_array_elements(NEW.feature_vector)
    LOOP
        IF jsonb_typeof(item) <> 'number' THEN
            RAISE EXCEPTION 'Features must be numeric.';
        END IF;

        IF (item #>> '{}')::DOUBLE PRECISION
            IN (
                'Infinity'::DOUBLE PRECISION,
                '-Infinity'::DOUBLE PRECISION
            )
        THEN
            RAISE EXCEPTION 'Infinite feature value rejected.';
        END IF;
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_sample_features
BEFORE INSERT OR UPDATE OF feature_vector, dataset_id
ON classification_samples
FOR EACH ROW
EXECUTE FUNCTION validate_sample_features();

-- ------------------------------------------------------------
-- 16. PREDICTION OWNERSHIP VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_prediction_relationship()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    sample_dataset BIGINT;
    associated_dataset BOOLEAN;
BEGIN
    SELECT dataset_id
    INTO sample_dataset
    FROM classification_samples
    WHERE sample_id = NEW.sample_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Prediction sample does not exist.';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM experiment_datasets
        WHERE experiment_id = NEW.experiment_id
          AND dataset_id = sample_dataset
    )
    INTO associated_dataset;

    IF NOT associated_dataset THEN
        RAISE EXCEPTION
            'Sample dataset is not associated with experiment.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prediction_relationship
BEFORE INSERT OR UPDATE OF experiment_id, sample_id
ON predictions
FOR EACH ROW
EXECUTE FUNCTION validate_prediction_relationship();

-- ------------------------------------------------------------
-- 17. EXPERIMENT STATE VALIDATION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'TRAINING' THEN
        IF NOT validate_parameter_configuration(NEW.experiment_id) THEN
            RAISE EXCEPTION 'Invalid parameter configuration.';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM experiment_datasets
            WHERE experiment_id = NEW.experiment_id
              AND training_enabled = TRUE
        ) THEN
            RAISE EXCEPTION 'No training dataset associated.';
        END IF;

        NEW.started_at := COALESCE(
            NEW.started_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    IF NEW.status IN ('TRAINED', 'EVALUATED') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM optimization_runs
            WHERE experiment_id = NEW.experiment_id
              AND status = 'COMPLETED'
        ) THEN
            RAISE EXCEPTION 'No completed optimization run exists.';
        END IF;
    END IF;

    IF NEW.status IN ('EVALUATED', 'ARCHIVED') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM evaluation_metrics
            WHERE experiment_id = NEW.experiment_id
        ) THEN
            RAISE EXCEPTION 'Evaluation metrics are required.';
        END IF;
    END IF;

    IF NEW.status IN ('TRAINED', 'EVALUATED', 'ARCHIVED', 'FAILED') THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_state
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION validate_experiment_transition();

-- ------------------------------------------------------------
-- 18. EVALUATION REPORTING VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_performance AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    r.run_id,
    r.run_number,
    m.evaluated_split,
    m.accuracy,
    m.precision_score,
    m.recall_score,
    m.f1_score,
    m.cross_entropy_loss,
    m.evaluated_at
FROM experiments e
JOIN optimization_runs r
    ON r.experiment_id = e.experiment_id
JOIN evaluation_metrics m
    ON m.run_id = r.run_id
   AND m.experiment_id = e.experiment_id;

-- ------------------------------------------------------------
-- 19. CLASSIFICATION REPORT VIEW
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW prediction_audit AS
SELECT
    p.prediction_id,
    e.experiment_name,
    s.sample_reference,
    s.label AS actual_label,
    p.predicted_label,
    p.predicted_probability,
    CASE
        WHEN p.predicted_label IS NULL THEN NULL
        ELSE p.predicted_label = s.label
    END AS is_correct,
    p.status,
    p.created_at
FROM predictions p
JOIN experiments e
    ON e.experiment_id = p.experiment_id
JOIN classification_samples s
    ON s.sample_id = p.sample_id;

-- ------------------------------------------------------------
-- 20. REPORTING FUNCTION
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION experiment_summary(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    experiment_name VARCHAR,
    experiment_state experiment_status,
    parameter_count BIGINT,
    training_samples BIGINT,
    completed_runs BIGINT,
    latest_loss DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        e.experiment_name,
        e.status,
        (
            SELECT COUNT(*)
            FROM variational_parameters vp
            WHERE vp.experiment_id = e.experiment_id
        ),
        (
            SELECT COUNT(*)
            FROM experiment_datasets ed
            JOIN classification_samples s
                ON s.dataset_id = ed.dataset_id
            WHERE ed.experiment_id = e.experiment_id
              AND s.data_split = 'TRAIN'
        ),
        (
            SELECT COUNT(*)
            FROM optimization_runs r
            WHERE r.experiment_id = e.experiment_id
              AND r.status = 'COMPLETED'
        ),
        (
            SELECT r.final_loss
            FROM optimization_runs r
            WHERE r.experiment_id = e.experiment_id
            ORDER BY r.run_number DESC
            LIMIT 1
        )
    FROM experiments e
    WHERE e.experiment_id = p_experiment_id;
$$;

-- ------------------------------------------------------------
-- 21. TRANSACTIONAL EPOCH RECORDING PROCEDURE
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE record_training_epoch(
    p_run_id BIGINT,
    p_epoch_number INTEGER,
    p_loss DOUBLE PRECISION,
    p_gradient_norm DOUBLE PRECISION,
    p_learning_rate DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status optimization_status;
BEGIN
    SELECT status
    INTO current_status
    FROM optimization_runs
    WHERE run_id = p_run_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Optimization run does not exist.';
    END IF;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Run is not active.';
    END IF;

    IF p_epoch_number < 0 OR p_loss < 0 OR
       p_gradient_norm < 0 OR
       p_learning_rate <= 0 OR p_learning_rate > 1 THEN
        RAISE EXCEPTION 'Invalid epoch values.';
    END IF;

    INSERT INTO training_epochs (
        run_id,
        epoch_number,
        training_loss,
        gradient_norm,
        learning_rate
    )
    VALUES (
        p_run_id,
        p_epoch_number,
        p_loss,
        p_gradient_norm,
        p_learning_rate
    );

    UPDATE optimization_runs
    SET epochs_completed = GREATEST(
        epochs_completed,
        p_epoch_number + 1
    )
    WHERE run_id = p_run_id;
END;
$$;

-- ------------------------------------------------------------
-- 22. SAMPLE DATA
-- ------------------------------------------------------------

INSERT INTO experiments (
    experiment_name,
    description,
    circuit_depth,
    feature_count,
    trainable_parameter_count,
    learning_rate,
    epoch_limit
)
VALUES (
    'two_qubit_vqc_binary_classification',
    'Two-qubit variational quantum classifier with RY feature encoding and CNOT entanglement.',
    3,
    2,
    4,
    0.08,
    120
);

INSERT INTO datasets (
    dataset_name,
    feature_count,
    source_description
)
VALUES (
    'synthetic_binary_quantum_dataset',
    2,
    'Deterministic two-feature binary classification dataset.'
);

INSERT INTO experiment_datasets (
    experiment_id,
    dataset_id,
    training_enabled
)
VALUES (1, 1, TRUE);

INSERT INTO circuit_layers (
    experiment_id,
    layer_number,
    layer_type,
    gate_configuration
)
VALUES
(
    1,
    0,
    'FEATURE_MAP',
    '{"gates":["RY(0,x0)","RY(1,x1)"]}'
),
(
    1,
    1,
    'ENTANGLING',
    '{"gates":["CNOT(0,1)"]}'
),
(
    1,
    2,
    'VARIATIONAL',
    '{"gates":["RY(0,t0)","RY(1,t1)","CNOT(0,1)","RY(0,t2)","RY(1,t3)"]}'
),
(
    1,
    3,
    'MEASUREMENT',
    '{"observable":"Pauli-Z","qubit":0}'
);

INSERT INTO variational_parameters (
    experiment_id,
    parameter_index,
    parameter_value
)
VALUES
    (1, 0, 0.10),
    (1, 1, -0.20),
    (1, 2, 0.30),
    (1, 3, -0.15);

INSERT INTO classification_samples (
    dataset_id,
    sample_reference,
    feature_vector,
    label,
    data_split
)
VALUES
    (1, 'S001', '[0.15, 0.20]', 'NEGATIVE', 'TRAIN'),
    (1, 'S002', '[0.35, 0.25]', 'NEGATIVE', 'TRAIN'),
    (1, 'S003', '[0.20, 0.55]', 'NEGATIVE', 'TRAIN'),
    (1, 'S004', '[0.55, 0.30]', 'NEGATIVE', 'TRAIN'),
    (1, 'S005', '[2.10, 2.00]', 'POSITIVE', 'TRAIN'),
    (1, 'S006', '[2.40, 1.80]', 'POSITIVE', 'TRAIN'),
    (1, 'S007', '[1.90, 2.45]', 'POSITIVE', 'TRAIN'),
    (1, 'S008', '[2.65, 2.30]', 'POSITIVE', 'TRAIN'),
    (1, 'S009', '[0.40, 0.65]', 'NEGATIVE', 'TEST'),
    (1, 'S010', '[2.20, 2.70]', 'POSITIVE', 'TEST');

-- ------------------------------------------------------------
-- 23. VALIDATION EXAMPLES
-- ------------------------------------------------------------

SELECT *
FROM validate_experiment_dataset(1, 1);

SELECT validate_parameter_configuration(1)
    AS parameter_configuration_valid;

-- ------------------------------------------------------------
-- 24. OPTIMIZATION WORKFLOW
-- ------------------------------------------------------------

INSERT INTO optimization_runs (
    experiment_id,
    run_number,
    status,
    initial_loss
)
VALUES (
    1,
    1,
    'RUNNING',
    0.693147
);

-- Record representative epoch history.
CALL record_training_epoch(1, 0, 0.693147, 0.250, 0.08);
CALL record_training_epoch(1, 1, 0.671000, 0.225, 0.08);
CALL record_training_epoch(1, 2, 0.642000, 0.190, 0.08);
CALL record_training_epoch(1, 3, 0.610000, 0.170, 0.08);

UPDATE optimization_runs
SET
    status = 'COMPLETED',
    final_loss = 0.610000,
    completed_at = CURRENT_TIMESTAMP
WHERE run_id = 1;

UPDATE experiments
SET status = 'TRAINING'
WHERE experiment_id = 1;

UPDATE experiments
SET status = 'TRAINED'
WHERE experiment_id = 1;

-- ------------------------------------------------------------
-- 25. EVALUATION METRICS
-- ------------------------------------------------------------

INSERT INTO evaluation_metrics (
    experiment_id,
    run_id,
    evaluated_split,
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    cross_entropy_loss,
    true_positive,
    false_positive,
    true_negative,
    false_negative
)
VALUES
(
    1,
    1,
    'TRAIN',
    0.875,
    0.833333,
    1.0,
    0.909091,
    0.610000,
    4,
    1,
    3,
    0
),
(
    1,
    1,
    'TEST',
    1.0,
    1.0,
    1.0,
    1.0,
    0.420000,
    1,
    0,
    1,
    0
);

UPDATE experiments
SET status = 'EVALUATED'
WHERE experiment_id = 1;

-- ------------------------------------------------------------
-- 26. SAMPLE PREDICTIONS
-- ------------------------------------------------------------

INSERT INTO predictions (
    experiment_id,
    sample_id,
    run_id,
    predicted_probability,
    predicted_label,
    status,
    inference_time_ms
)
VALUES
    (1, 9, 1, 0.12, 'NEGATIVE', 'COMPLETED', 0.85),
    (1, 10, 1, 0.91, 'POSITIVE', 'COMPLETED', 0.79);

-- ------------------------------------------------------------
-- 27. RETRIEVAL QUERIES
-- ------------------------------------------------------------

SELECT
    experiment_name,
    status,
    qubit_count,
    circuit_depth,
    trainable_parameter_count,
    learning_rate
FROM experiments
ORDER BY created_at DESC;

SELECT
    sample_reference,
    feature_vector,
    label,
    data_split
FROM classification_samples
WHERE dataset_id = 1
ORDER BY sample_id;

SELECT
    parameter_index,
    parameter_value,
    parameter_group
FROM variational_parameters
WHERE experiment_id = 1
ORDER BY parameter_index;

-- ------------------------------------------------------------
-- 28. VALIDATION AND FAILURE REPORTING
-- ------------------------------------------------------------

SELECT
    dataset_name,
    feature_count,
    total_samples
FROM datasets
WHERE feature_count <> 2;

SELECT
    experiment_id,
    experiment_name
FROM experiments
WHERE NOT validate_parameter_configuration(experiment_id);

SELECT
    dataset_id,
    data_split,
    COUNT(*) AS sample_count,
    COUNT(*) FILTER (
        WHERE label = 'POSITIVE'
    ) AS positive_samples,
    COUNT(*) FILTER (
        WHERE label = 'NEGATIVE'
    ) AS negative_samples
FROM classification_samples
GROUP BY dataset_id, data_split
ORDER BY dataset_id, data_split;

-- ------------------------------------------------------------
-- 29. AGGREGATION AND REPORTING
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    r.run_number,
    COUNT(te.epoch_id) AS recorded_epochs,
    MIN(te.training_loss) AS minimum_loss,
    MAX(te.training_loss) AS maximum_loss,
    AVG(te.training_loss) AS average_loss
FROM experiments e
JOIN optimization_runs r
    ON r.experiment_id = e.experiment_id
LEFT JOIN training_epochs te
    ON te.run_id = r.run_id
GROUP BY e.experiment_name, r.run_number;

SELECT *
FROM experiment_performance
ORDER BY evaluated_at DESC;

SELECT *
FROM prediction_audit
ORDER BY prediction_id;

SELECT *
FROM experiment_summary(1);

-- ------------------------------------------------------------
-- 30. ELIGIBILITY AND MODEL COMPLETION REPORT
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    validate_parameter_configuration(e.experiment_id)
        AS parameters_valid,
    EXISTS (
        SELECT 1
        FROM experiment_datasets ed
        JOIN classification_samples s
            ON s.dataset_id = ed.dataset_id
        WHERE ed.experiment_id = e.experiment_id
          AND s.data_split = 'TRAIN'
          AND s.label = 'POSITIVE'
    ) AS positive_training_class_available,
    EXISTS (
        SELECT 1
        FROM experiment_datasets ed
        JOIN classification_samples s
            ON s.dataset_id = ed.dataset_id
        WHERE ed.experiment_id = e.experiment_id
          AND s.data_split = 'TRAIN'
          AND s.label = 'NEGATIVE'
    ) AS negative_training_class_available,
    EXISTS (
        SELECT 1
        FROM optimization_runs r
        WHERE r.experiment_id = e.experiment_id
          AND r.status = 'COMPLETED'
    ) AS completed_training_exists,
    EXISTS (
        SELECT 1
        FROM evaluation_metrics m
        WHERE m.experiment_id = e.experiment_id
          AND m.evaluated_split = 'TEST'
    ) AS test_evaluation_exists
FROM experiments e;

-- ------------------------------------------------------------
-- 31. QUERY PLAN EXAMPLE
-- ------------------------------------------------------------

EXPLAIN ANALYZE
SELECT
    sample_reference,
    label
FROM classification_samples
WHERE dataset_id = 1
  AND data_split = 'TRAIN';

-- ------------------------------------------------------------
-- 32. FINAL INTEGRITY CHECK
-- ------------------------------------------------------------

DO $$
BEGIN
    IF NOT validate_parameter_configuration(1) THEN
        RAISE EXCEPTION 'Parameter integrity validation failed.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM evaluation_metrics
        WHERE experiment_id = 1
          AND evaluated_split = 'TEST'
    ) THEN
        RAISE EXCEPTION 'Test evaluation is missing.';
    END IF;

    RAISE NOTICE 'Quantum experiment integrity checks passed.';
END;
$$;

COMMIT;
