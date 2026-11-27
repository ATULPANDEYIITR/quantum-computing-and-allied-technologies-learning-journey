/*
===============================================================================
QUANTUM GENERATIVE MODELS
PostgreSQL 15+

Relational experiment-management system for quantum generative learning.

Models:
- Quantum model architectures
- Parameterized quantum circuits
- Circuit gates and parameters
- Training datasets and target distributions
- Experiment configurations and execution states
- Measurement samples
- Evaluation metrics
- Training history
- Model validation and experiment reporting

The database stores experiment configurations, results, and measurements.
Quantum circuit execution is performed by the application layer.
===============================================================================
*/

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_learning;

SET search_path TO quantum_learning, public;

-- ============================================================================
-- 1. DOMAIN TYPES
-- ============================================================================

CREATE TYPE model_family AS ENUM (
    'QUANTUM_BORN_MACHINE',
    'QUANTUM_GAN',
    'QUANTUM_VAE',
    'QUANTUM_BOLTZMANN_MACHINE',
    'QUANTUM_CIRCUIT_GENERATOR'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE gate_type AS ENUM (
    'H',
    'X',
    'Y',
    'Z',
    'RX',
    'RY',
    'RZ',
    'CNOT',
    'CZ',
    'SWAP'
);

CREATE TYPE optimizer_type AS ENUM (
    'SPSA',
    'ADAM',
    'SGD',
    'COBYLA',
    'PARAMETER_SHIFT'
);

CREATE TYPE metric_type AS ENUM (
    'KL_DIVERGENCE',
    'JENSEN_SHANNON_DIVERGENCE',
    'TOTAL_VARIATION',
    'FIDELITY',
    'GENERATED_ENTROPY',
    'TARGET_ENTROPY',
    'RECONSTRUCTION_ERROR',
    'GENERATOR_LOSS',
    'DISCRIMINATOR_LOSS'
);

-- ============================================================================
-- 2. USERS AND PROJECTS
-- ============================================================================

CREATE TABLE research_projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    owner_name VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(30) NOT NULL CHECK (
        role IN ('ADMIN', 'RESEARCHER', 'REVIEWER', 'VIEWER')
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. QUANTUM MODELS
-- ============================================================================

CREATE TABLE quantum_models (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES research_projects(project_id),

    model_name VARCHAR(150) NOT NULL,

    family model_family NOT NULL,

    description TEXT,

    qubit_count SMALLINT NOT NULL CHECK (
        qubit_count BETWEEN 1 AND 30
    ),

    circuit_depth INTEGER NOT NULL CHECK (
        circuit_depth > 0
    ),

    parameter_count INTEGER NOT NULL CHECK (
        parameter_count >= 0
    ),

    is_trainable BOOLEAN NOT NULL DEFAULT TRUE,

    created_by BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, model_name)
);

CREATE INDEX idx_models_project
ON quantum_models(project_id);

CREATE INDEX idx_models_family
ON quantum_models(family);

-- ============================================================================
-- 4. CIRCUITS AND GATES
-- ============================================================================

CREATE TABLE quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES quantum_models(model_id)
        ON DELETE CASCADE,

    circuit_name VARCHAR(150) NOT NULL,

    circuit_version INTEGER NOT NULL DEFAULT 1
        CHECK (circuit_version > 0),

    qubit_count SMALLINT NOT NULL CHECK (
        qubit_count BETWEEN 1 AND 30
    ),

    depth INTEGER NOT NULL CHECK (depth > 0),

    description TEXT,

    UNIQUE(model_id, circuit_name, circuit_version)
);

CREATE TABLE circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id)
        ON DELETE CASCADE,

    gate_sequence INTEGER NOT NULL CHECK (
        gate_sequence >= 0
    ),

    gate gate_type NOT NULL,

    target_qubit SMALLINT NOT NULL CHECK (
        target_qubit >= 0
    ),

    control_qubit SMALLINT,

    rotation_angle DOUBLE PRECISION,

    parameterized BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(circuit_id, gate_sequence),

    CHECK (
        (gate IN ('CNOT', 'CZ') AND control_qubit IS NOT NULL)
        OR
        (gate NOT IN ('CNOT', 'CZ') AND control_qubit IS NULL)
    ),

    CHECK (
        control_qubit IS NULL
        OR control_qubit <> target_qubit
    ),

    CHECK (
        (gate IN ('RX', 'RY', 'RZ') AND rotation_angle IS NOT NULL)
        OR
        (gate NOT IN ('RX', 'RY', 'RZ') AND rotation_angle IS NULL)
    ),

    CHECK (
        rotation_angle IS NULL
        OR rotation_angle NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE INDEX idx_circuit_gates_order
ON circuit_gates(circuit_id, gate_sequence);

-- ============================================================================
-- 5. MODEL PARAMETERS
-- ============================================================================

CREATE TABLE model_parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    model_id BIGINT NOT NULL
        REFERENCES quantum_models(model_id)
        ON DELETE CASCADE,

    parameter_name VARCHAR(100) NOT NULL,

    parameter_index INTEGER NOT NULL CHECK (
        parameter_index >= 0
    ),

    parameter_value DOUBLE PRECISION NOT NULL,

    trainable BOOLEAN NOT NULL DEFAULT TRUE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(model_id, parameter_index),

    CHECK (
        parameter_value NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE INDEX idx_parameters_model
ON model_parameters(model_id, parameter_index);

-- ============================================================================
-- 6. DATASETS AND TARGET DISTRIBUTIONS
-- ============================================================================

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES research_projects(project_id),

    dataset_name VARCHAR(150) NOT NULL,

    dataset_version VARCHAR(30) NOT NULL,

    dataset_type VARCHAR(30) NOT NULL CHECK (
        dataset_type IN (
            'SYNTHETIC',
            'BINARY',
            'TABULAR',
            'IMAGE',
            'QUANTUM_STATE'
        )
    ),

    feature_count INTEGER NOT NULL CHECK (
        feature_count > 0
    ),

    record_count BIGINT NOT NULL CHECK (
        record_count > 0
    ),

    source_description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(project_id, dataset_name, dataset_version)
);

CREATE TABLE target_distributions (
    distribution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id)
        ON DELETE CASCADE,

    outcome_index INTEGER NOT NULL CHECK (
        outcome_index >= 0
    ),

    binary_state VARCHAR(30) NOT NULL,

    probability DOUBLE PRECISION NOT NULL CHECK (
        probability BETWEEN 0 AND 1
    ),

    UNIQUE(dataset_id, outcome_index),
    UNIQUE(dataset_id, binary_state),

    CHECK (
        probability NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE INDEX idx_distribution_dataset
ON target_distributions(dataset_id);

-- ============================================================================
-- 7. EXPERIMENT CONFIGURATIONS
-- ============================================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    project_id BIGINT NOT NULL
        REFERENCES research_projects(project_id),

    model_id BIGINT NOT NULL
        REFERENCES quantum_models(model_id),

    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id),

    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),

    researcher_id BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    optimizer optimizer_type NOT NULL,

    learning_rate DOUBLE PRECISION NOT NULL CHECK (
        learning_rate > 0 AND learning_rate < 1
    ),

    iteration_limit INTEGER NOT NULL CHECK (
        iteration_limit > 0
    ),

    measurement_shots INTEGER NOT NULL CHECK (
        measurement_shots > 0
    ),

    random_seed BIGINT NOT NULL,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    initial_loss DOUBLE PRECISION,

    final_loss DOUBLE PRECISION,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        initial_loss IS NULL OR initial_loss >= 0
    ),

    CHECK (
        final_loss IS NULL OR final_loss >= 0
    ),

    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    )
);

CREATE INDEX idx_experiments_project_status
ON experiments(project_id, status);

CREATE INDEX idx_experiments_model_created
ON experiments(model_id, created_at DESC);

CREATE INDEX idx_experiments_researcher
ON experiments(researcher_id, created_at DESC);

-- ============================================================================
-- 8. TRAINING HISTORY
-- ============================================================================

CREATE TABLE training_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    iteration INTEGER NOT NULL CHECK (
        iteration > 0
    ),

    training_loss DOUBLE PRECISION NOT NULL CHECK (
        training_loss >= 0
    ),

    learning_rate DOUBLE PRECISION NOT NULL CHECK (
        learning_rate > 0
    ),

    gradient_norm DOUBLE PRECISION,

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, iteration),

    CHECK (
        gradient_norm IS NULL OR gradient_norm >= 0
    ),

    CHECK (
        training_loss NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE INDEX idx_training_history_experiment
ON training_history(experiment_id, iteration);

-- ============================================================================
-- 9. QUANTUM MEASUREMENT SAMPLES
-- ============================================================================

CREATE TABLE measurement_samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    measured_state VARCHAR(30) NOT NULL,

    outcome_index INTEGER NOT NULL CHECK (
        outcome_index >= 0
    ),

    measurement_count BIGINT NOT NULL CHECK (
        measurement_count > 0
    ),

    measured_probability DOUBLE PRECISION NOT NULL CHECK (
        measured_probability BETWEEN 0 AND 1
    ),

    UNIQUE(experiment_id, measured_state),
    UNIQUE(experiment_id, outcome_index)
);

CREATE INDEX idx_measurements_experiment
ON measurement_samples(experiment_id);

-- ============================================================================
-- 10. EVALUATION METRICS
-- ============================================================================

CREATE TABLE evaluation_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    metric metric_type NOT NULL,

    metric_value DOUBLE PRECISION NOT NULL,

    evaluation_stage VARCHAR(30) NOT NULL CHECK (
        evaluation_stage IN (
            'INITIAL',
            'TRAINING',
            'FINAL',
            'VALIDATION'
        )
    ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        metric_value NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    ),

    UNIQUE(experiment_id, metric, evaluation_stage)
);

CREATE INDEX idx_metrics_experiment
ON evaluation_metrics(experiment_id, metric);

-- ============================================================================
-- 11. EXPERIMENT VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_experiment_configuration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    model_qubits SMALLINT;
    circuit_qubits SMALLINT;
    circuit_model BIGINT;
    dataset_project BIGINT;
    distribution_total DOUBLE PRECISION;
    outcome_count BIGINT;
BEGIN
    SELECT qubit_count
    INTO model_qubits
    FROM quantum_models
    WHERE model_id = NEW.model_id;

    SELECT qubit_count, model_id
    INTO circuit_qubits, circuit_model
    FROM quantum_circuits
    WHERE circuit_id = NEW.circuit_id;

    SELECT project_id
    INTO dataset_project
    FROM datasets
    WHERE dataset_id = NEW.dataset_id;

    IF model_qubits IS NULL OR circuit_qubits IS NULL THEN
        RAISE EXCEPTION 'Model or circuit does not exist.';
    END IF;

    IF model_qubits <> circuit_qubits THEN
        RAISE EXCEPTION
            'Model and circuit qubit counts differ.';
    END IF;

    IF circuit_model <> NEW.model_id THEN
        RAISE EXCEPTION
            'Circuit does not belong to the selected model.';
    END IF;

    IF dataset_project <> NEW.project_id THEN
        RAISE EXCEPTION
            'Dataset and experiment projects differ.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM researchers
        WHERE researcher_id = NEW.researcher_id
          AND active = TRUE
          AND role IN ('ADMIN', 'RESEARCHER')
    ) THEN
        RAISE EXCEPTION
            'Researcher is not authorized to execute experiments.';
    END IF;

    SELECT COUNT(*), COALESCE(SUM(probability), 0)
    INTO outcome_count, distribution_total
    FROM target_distributions
    WHERE dataset_id = NEW.dataset_id;

    IF outcome_count <> (1::BIGINT << model_qubits) THEN
        RAISE EXCEPTION
            'Target distribution must contain exactly 2^qubits outcomes.';
    END IF;

    IF ABS(distribution_total - 1.0) > 0.000001 THEN
        RAISE EXCEPTION
            'Target probabilities must sum to one.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment
BEFORE INSERT ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_configuration();

-- ============================================================================
-- 12. EXPERIMENT STATE TRANSITION ENFORCEMENT
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        RAISE EXCEPTION
            'Terminal experiment states cannot be changed.';
    END IF;

    IF NOT (
        (OLD.status = 'CREATED'
            AND NEW.status IN ('VALIDATED', 'CANCELLED'))
        OR
        (OLD.status = 'VALIDATED'
            AND NEW.status IN ('RUNNING', 'FAILED', 'CANCELLED'))
        OR
        (OLD.status = 'RUNNING'
            AND NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED'))
    ) THEN
        RAISE EXCEPTION
            'Invalid experiment state transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status = 'FAILED'
       AND NULLIF(TRIM(NEW.failure_reason), '') IS NULL THEN
        RAISE EXCEPTION
            'Failed experiments require a failure reason.';
    END IF;

    IF NEW.status = 'COMPLETED' AND NEW.final_loss IS NULL THEN
        RAISE EXCEPTION
            'Completed experiments require final loss.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ============================================================================
-- 13. TRAINING HISTORY VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_training_iteration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_limit INTEGER;
    current_status experiment_status;
BEGIN
    SELECT iteration_limit, status
    INTO experiment_limit, current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Training history requires a running experiment.';
    END IF;

    IF NEW.iteration > experiment_limit THEN
        RAISE EXCEPTION
            'Iteration exceeds experiment limit.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_training_iteration
BEFORE INSERT ON training_history
FOR EACH ROW
EXECUTE FUNCTION validate_training_iteration();

-- ============================================================================
-- 14. MEASUREMENT VALIDATION
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_measurement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    model_qubits SMALLINT;
    configured_shots INTEGER;
    current_status experiment_status;
BEGIN
    SELECT m.qubit_count, e.measurement_shots, e.status
    INTO model_qubits, configured_shots, current_status
    FROM experiments e
    JOIN quantum_models m ON m.model_id = e.model_id
    WHERE e.experiment_id = NEW.experiment_id;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Measurements require a running experiment.';
    END IF;

    IF length(NEW.measured_state) <> model_qubits THEN
        RAISE EXCEPTION
            'Measurement state has incorrect binary length.';
    END IF;

    IF NEW.measured_state !~ '^[01]+$' THEN
        RAISE EXCEPTION
            'Measurement state must contain binary digits.';
    END IF;

    IF NEW.outcome_index >= (1::BIGINT << model_qubits) THEN
        RAISE EXCEPTION 'Invalid measurement outcome index.';
    END IF;

    IF NEW.measured_state::bit(30)::bigint IS NULL THEN
        RAISE EXCEPTION 'Invalid measurement state.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT ON measurement_samples
FOR EACH ROW
EXECUTE FUNCTION validate_measurement();

-- ============================================================================
-- 15. DISTRIBUTION REPORTING VIEW
-- ============================================================================

CREATE OR REPLACE VIEW experiment_distribution_report AS
SELECT
    e.experiment_id,
    e.experiment_code,
    e.status,
    e.measurement_shots,
    ms.measured_state,
    ms.outcome_index,
    ms.measurement_count,
    ms.measured_probability,
    td.probability AS target_probability,
    ABS(
        ms.measured_probability - td.probability
    ) AS absolute_error
FROM experiments e
JOIN measurement_samples ms
    ON ms.experiment_id = e.experiment_id
JOIN target_distributions td
    ON td.dataset_id = e.dataset_id
   AND td.outcome_index = ms.outcome_index;

-- ============================================================================
-- 16. MODEL PERFORMANCE REPORT
-- ============================================================================

CREATE OR REPLACE VIEW experiment_performance_report AS
SELECT
    e.experiment_id,
    e.experiment_code,
    p.project_name,
    qm.model_name,
    qm.family,
    qm.qubit_count,
    e.optimizer,
    e.status,
    e.iteration_limit,
    e.initial_loss,
    e.final_loss,
    e.started_at,
    e.completed_at,
    (
        SELECT metric_value
        FROM evaluation_metrics em
        WHERE em.experiment_id = e.experiment_id
          AND em.metric = 'TOTAL_VARIATION'
          AND em.evaluation_stage = 'FINAL'
    ) AS final_total_variation,
    (
        SELECT COUNT(*)
        FROM training_history th
        WHERE th.experiment_id = e.experiment_id
    ) AS recorded_iterations
FROM experiments e
JOIN research_projects p ON p.project_id = e.project_id
JOIN quantum_models qm ON qm.model_id = e.model_id;

-- ============================================================================
-- 17. ELIGIBILITY FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION experiment_eligibility(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    experiment_id BIGINT,
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_row experiments%ROWTYPE;
    distribution_total DOUBLE PRECISION;
    outcome_count BIGINT;
    history_count BIGINT;
BEGIN
    SELECT *
    INTO experiment_row
    FROM experiments
    WHERE experiments.experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT
            p_experiment_id,
            FALSE,
            'Experiment does not exist'::TEXT;
        RETURN;
    END IF;

    IF experiment_row.status <> 'RUNNING' THEN
        RETURN QUERY SELECT
            p_experiment_id,
            FALSE,
            'Experiment is not running'::TEXT;
        RETURN;
    END IF;

    SELECT COUNT(*), COALESCE(SUM(probability), 0)
    INTO outcome_count, distribution_total
    FROM target_distributions
    WHERE dataset_id = experiment_row.dataset_id;

    IF outcome_count <> (
        SELECT 1::BIGINT << qubit_count
        FROM quantum_models
        WHERE model_id = experiment_row.model_id
    ) THEN
        RETURN QUERY SELECT
            p_experiment_id,
            FALSE,
            'Incomplete target distribution'::TEXT;
        RETURN;
    END IF;

    IF ABS(distribution_total - 1.0) > 0.000001 THEN
        RETURN QUERY SELECT
            p_experiment_id,
            FALSE,
            'Target distribution is not normalized'::TEXT;
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO history_count
    FROM training_history
    WHERE training_history.experiment_id = p_experiment_id;

    IF history_count >= experiment_row.iteration_limit THEN
        RETURN QUERY SELECT
            p_experiment_id,
            FALSE,
            'Training iteration limit reached'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT
        p_experiment_id,
        TRUE,
        'Experiment configuration is valid'::TEXT;
END;
$$;

-- ============================================================================
-- 18. AGGREGATION FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION get_measurement_statistics(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    total_shots BIGINT,
    distinct_outcomes BIGINT,
    empirical_entropy DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        COALESCE(SUM(measurement_count), 0)::BIGINT,
        COUNT(*)::BIGINT,
        COALESCE(
            -SUM(
                CASE
                    WHEN measurement_count > 0 THEN
                        (measurement_count::DOUBLE PRECISION /
                         NULLIF(
                             SUM(measurement_count) OVER (),
                             0
                         ))
                        *
                        LN(
                            measurement_count::DOUBLE PRECISION /
                            NULLIF(
                                SUM(measurement_count) OVER (),
                                0
                            )
                        )
                    ELSE 0
                END
            ),
            0
        )::DOUBLE PRECISION
    FROM measurement_samples
    WHERE experiment_id = p_experiment_id;
$$;

-- ============================================================================
-- 19. SAMPLE DATA
-- ============================================================================

INSERT INTO research_projects (
    project_name,
    description,
    owner_name
)
VALUES (
    'Quantum Generative Learning Laboratory',
    'Parameterized quantum circuits and Born machine experiments.',
    'Research Administration'
);

INSERT INTO researchers (
    username,
    email,
    role
)
VALUES
(
    'quantum_admin',
    'admin@example.org',
    'ADMIN'
),
(
    'researcher_one',
    'researcher@example.org',
    'RESEARCHER'
),
(
    'reviewer_one',
    'reviewer@example.org',
    'REVIEWER'
),
(
    'viewer_one',
    'viewer@example.org',
    'VIEWER'
);

INSERT INTO quantum_models (
    project_id,
    model_name,
    family,
    description,
    qubit_count,
    circuit_depth,
    parameter_count,
    created_by
)
VALUES (
    1,
    'Two-Qubit Quantum Born Machine',
    'QUANTUM_BORN_MACHINE',
    'Parameterized circuit generating a binary probability distribution.',
    2,
    3,
    4,
    1
);

INSERT INTO quantum_circuits (
    model_id,
    circuit_name,
    circuit_version,
    qubit_count,
    depth,
    description
)
VALUES (
    1,
    'RY-CNOT-RY Circuit',
    1,
    2,
    3,
    'Two rotation layers separated by an entangling layer.'
);

INSERT INTO circuit_gates (
    circuit_id,
    gate_sequence,
    gate,
    target_qubit,
    rotation_angle,
    parameterized
)
VALUES
(1, 1, 'RY', 0, 0.50, TRUE),
(1, 2, 'RY', 1, 0.30, TRUE),
(1, 3, 'CNOT', 1, NULL, FALSE),
(1, 4, 'RY', 0, 0.20, TRUE),
(1, 5, 'RY', 1, 0.70, TRUE);

INSERT INTO model_parameters (
    model_id,
    parameter_name,
    parameter_index,
    parameter_value,
    trainable
)
VALUES
(1, 'theta_0', 0, 0.50, TRUE),
(1, 'theta_1', 1, 0.30, TRUE),
(1, 'theta_2', 2, 0.20, TRUE),
(1, 'theta_3', 3, 0.70, TRUE);

INSERT INTO datasets (
    project_id,
    dataset_name,
    dataset_version,
    dataset_type,
    feature_count,
    record_count,
    source_description
)
VALUES (
    1,
    'Synthetic Binary Distribution',
    '1.0',
    'BINARY',
    2,
    10000,
    'Four-outcome normalized synthetic probability distribution.'
);

INSERT INTO target_distributions (
    dataset_id,
    outcome_index,
    binary_state,
    probability
)
VALUES
(1, 0, '00', 0.40),
(1, 1, '01', 0.10),
(1, 2, '10', 0.10),
(1, 3, '11', 0.40);

-- ============================================================================
-- 20. VALID EXPERIMENT
-- ============================================================================

INSERT INTO experiments (
    project_id,
    model_id,
    circuit_id,
    dataset_id,
    researcher_id,
    optimizer,
    learning_rate,
    iteration_limit,
    measurement_shots,
    random_seed
)
VALUES (
    1, 1, 1, 1, 2,
    'SPSA',
    0.08,
    300,
    5000,
    42
);

-- ============================================================================
-- 21. INVALID DISTRIBUTION EXAMPLE
-- ============================================================================
-- The following statement is intentionally excluded from execution because
-- it violates the unique outcome constraint.
--
-- INSERT INTO target_distributions
-- (dataset_id, outcome_index, binary_state, probability)
-- VALUES (1, 0, '00', 0.50);
--
-- An invalid experiment configuration can be tested inside a transaction
-- using SAVEPOINT and ROLLBACK TO SAVEPOINT.

SAVEPOINT invalid_experiment_test;

DO $$
BEGIN
    BEGIN
        INSERT INTO experiments (
            project_id,
            model_id,
            circuit_id,
            dataset_id,
            researcher_id,
            optimizer,
            learning_rate,
            iteration_limit,
            measurement_shots,
            random_seed
        )
        VALUES (
            1, 1, 1, 1, 4,
            'SPSA',
            0.08,
            300,
            5000,
            99
        );

        RAISE EXCEPTION
            'Expected authorization failure was not raised.';

    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE '%not authorized%' THEN
                RAISE;
            END IF;

            RAISE NOTICE
                'Invalid researcher correctly rejected: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_experiment_test;

-- ============================================================================
-- 22. WORKFLOW PROCESSING
-- ============================================================================

UPDATE experiments
SET status = 'VALIDATED'
WHERE experiment_id = 1;

UPDATE experiments
SET status = 'RUNNING',
    started_at = CURRENT_TIMESTAMP
WHERE experiment_id = 1
  AND status = 'VALIDATED';

-- Eligibility evaluation during execution.
SELECT *
FROM experiment_eligibility(1);

-- ============================================================================
-- 23. TRAINING RECORDS
-- ============================================================================

INSERT INTO training_history (
    experiment_id,
    iteration,
    training_loss,
    learning_rate,
    gradient_norm
)
VALUES
(1, 1, 0.180000, 0.035000, 0.120000),
(1, 2, 0.165000, 0.030000, 0.105000),
(1, 3, 0.150000, 0.027000, 0.091000),
(1, 4, 0.139000, 0.025000, 0.082000),
(1, 5, 0.128000, 0.023000, 0.073000);

-- ============================================================================
-- 24. MEASUREMENT RESULTS
-- ============================================================================

INSERT INTO measurement_samples (
    experiment_id,
    measured_state,
    outcome_index,
    measurement_count,
    measured_probability
)
VALUES
(1, '00', 0, 1980, 0.396),
(1, '01', 1, 520, 0.104),
(1, '10', 2, 490, 0.098),
(1, '11', 3, 2010, 0.402);

-- ============================================================================
-- 25. EVALUATION METRICS
-- ============================================================================

INSERT INTO evaluation_metrics (
    experiment_id,
    metric,
    metric_value,
    evaluation_stage
)
VALUES
(1, 'KL_DIVERGENCE', 0.000125, 'FINAL'),
(1, 'TOTAL_VARIATION', 0.006000, 'FINAL'),
(1, 'GENERATED_ENTROPY', 1.724000, 'FINAL'),
(1, 'TARGET_ENTROPY', 1.721928, 'FINAL');

-- ============================================================================
-- 26. COMPLETE EXPERIMENT
-- ============================================================================

UPDATE experiments
SET status = 'COMPLETED',
    initial_loss = 0.180000,
    final_loss = 0.000125
WHERE experiment_id = 1
  AND status = 'RUNNING';

-- ============================================================================
-- 27. RETRIEVAL QUERIES
-- ============================================================================

-- Retrieve all experiments and their model configurations.
SELECT
    e.experiment_code,
    qm.model_name,
    qm.family,
    qm.qubit_count,
    e.optimizer,
    e.status,
    e.final_loss
FROM experiments e
JOIN quantum_models qm
    ON qm.model_id = e.model_id
ORDER BY e.created_at DESC;

-- Retrieve circuit gate sequence.
SELECT
    qc.circuit_name,
    cg.gate_sequence,
    cg.gate,
    cg.target_qubit,
    cg.control_qubit,
    cg.rotation_angle
FROM quantum_circuits qc
JOIN circuit_gates cg
    ON cg.circuit_id = qc.circuit_id
WHERE qc.circuit_id = 1
ORDER BY cg.gate_sequence;

-- ============================================================================
-- 28. VALIDATION QUERIES
-- ============================================================================

-- Verify target distribution normalization.
SELECT
    dataset_id,
    SUM(probability) AS probability_sum,
    COUNT(*) AS outcomes,
    ABS(SUM(probability) - 1.0) < 0.000001 AS normalized
FROM target_distributions
GROUP BY dataset_id;

-- Verify measurement count consistency.
SELECT
    experiment_id,
    SUM(measurement_count) AS observed_shots,
    e.measurement_shots AS configured_shots,
    SUM(measurement_count) = e.measurement_shots AS shots_match
FROM measurement_samples ms
JOIN experiments e USING (experiment_id)
GROUP BY experiment_id, e.measurement_shots;

-- ============================================================================
-- 29. AGGREGATION AND EVALUATION
-- ============================================================================

SELECT *
FROM get_measurement_statistics(1);

SELECT
    experiment_id,
    SUM(
        ABS(measured_probability - target_probability)
    ) / 2.0 AS empirical_total_variation
FROM experiment_distribution_report
GROUP BY experiment_id;

-- ============================================================================
-- 30. TRAINING CONVERGENCE REPORT
-- ============================================================================

SELECT
    experiment_id,
    MIN(training_loss) AS minimum_loss,
    MAX(training_loss) AS maximum_loss,
    AVG(training_loss) AS average_loss,
    MIN(iteration) AS first_iteration,
    MAX(iteration) AS last_iteration
FROM training_history
GROUP BY experiment_id;

-- ============================================================================
-- 31. FINAL REPORT
-- ============================================================================

SELECT *
FROM experiment_performance_report;

SELECT
    measured_state,
    target_probability,
    measured_probability,
    absolute_error,
    measurement_count
FROM experiment_distribution_report
WHERE experiment_id = 1
ORDER BY outcome_index;

-- ============================================================================
-- 32. TRANSACTIONAL FAILURE HANDLING EXAMPLE
-- ============================================================================

SAVEPOINT invalid_transition_test;

DO $$
BEGIN
    BEGIN
        UPDATE experiments
        SET status = 'RUNNING'
        WHERE experiment_id = 1;

        RAISE EXCEPTION
            'Expected terminal-state transition failure.';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM NOT LIKE '%Terminal experiment states%' THEN
                RAISE;
            END IF;

            RAISE NOTICE
                'Terminal-state transition correctly rejected.';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_transition_test;

-- ============================================================================
-- 33. OPERATIONAL REPORTING
-- ============================================================================

SELECT
    status,
    COUNT(*) AS experiment_count,
    AVG(final_loss) AS average_final_loss
FROM experiments
GROUP BY status
ORDER BY status;

SELECT
    qm.family,
    COUNT(e.experiment_id) AS experiment_count,
    AVG(e.final_loss) AS average_final_loss
FROM quantum_models qm
LEFT JOIN experiments e
    ON e.model_id = qm.model_id
GROUP BY qm.family
ORDER BY experiment_count DESC;

-- ============================================================================
-- 34. COMMIT
-- ============================================================================

COMMIT;
