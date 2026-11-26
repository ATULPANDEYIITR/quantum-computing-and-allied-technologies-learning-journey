-- ============================================================
-- QUANTUM NEURAL NETWORKS: FUNDAMENTALS
-- PostgreSQL 15+
--
-- Relational experiment management for variational quantum
-- neural networks.
--
-- Models:
--   Experiments
--   Quantum circuits
--   Qubits
--   Quantum gates
--   Feature encodings
--   Trainable parameters
--   Training datasets
--   Measurement observables
--   Optimization runs
--   Measurements
--   Evaluation metrics
--   Experiment status and validation
--
-- The database stores experiment metadata and quantum
-- execution results. It does not simulate quantum hardware.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS qnn;

SET search_path TO qnn, public;

-- ------------------------------------------------------------
-- 1. Domain types
-- ------------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATING',
    'READY',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE circuit_status AS ENUM (
    'DRAFT',
    'VALIDATED',
    'DEPLOYED',
    'RETIRED'
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

CREATE TYPE encoding_type AS ENUM (
    'ANGLE',
    'BASIS',
    'AMPLITUDE',
    'IQP'
);

CREATE TYPE optimizer_type AS ENUM (
    'SGD',
    'ADAM',
    'RMSPROP',
    'SPSA',
    'COBYLA'
);

-- ------------------------------------------------------------
-- 2. Research projects
-- ------------------------------------------------------------

CREATE TABLE projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(150) NOT NULL UNIQUE,
    research_area VARCHAR(150) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 3. Quantum experiments
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    project_id BIGINT NOT NULL
        REFERENCES projects(project_id),

    experiment_name VARCHAR(180) NOT NULL,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    qubit_count INTEGER NOT NULL
        CHECK (qubit_count BETWEEN 1 AND 30),

    feature_count INTEGER NOT NULL
        CHECK (feature_count > 0),

    target_variable VARCHAR(100) NOT NULL,

    random_seed INTEGER NOT NULL DEFAULT 42,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    UNIQUE(project_id, experiment_name),

    CHECK (
        completed_at IS NULL OR started_at IS NOT NULL
    ),

    CHECK (
        status <> 'COMPLETED' OR completed_at IS NOT NULL
    ),

    CHECK (
        status <> 'FAILED' OR failure_reason IS NOT NULL
    )
);

CREATE INDEX idx_experiments_project_status
    ON experiments(project_id, status);

CREATE INDEX idx_experiments_created
    ON experiments(created_at DESC);

-- ------------------------------------------------------------
-- 4. Quantum circuits
-- ------------------------------------------------------------

CREATE TABLE quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    circuit_name VARCHAR(150) NOT NULL,

    architecture VARCHAR(100) NOT NULL,

    status circuit_status NOT NULL DEFAULT 'DRAFT',

    qubit_count INTEGER NOT NULL
        CHECK (qubit_count > 0),

    circuit_depth INTEGER NOT NULL
        CHECK (circuit_depth > 0),

    parameter_count INTEGER NOT NULL
        CHECK (parameter_count >= 0),

    encoding encoding_type NOT NULL,

    entanglement_strategy VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, circuit_name),

    UNIQUE(circuit_id, experiment_id)
);

CREATE INDEX idx_circuits_experiment
    ON quantum_circuits(experiment_id);

-- ------------------------------------------------------------
-- 5. Circuit gates
-- ------------------------------------------------------------

CREATE TABLE circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id)
        ON DELETE CASCADE,

    sequence_number INTEGER NOT NULL
        CHECK (sequence_number >= 0),

    gate gate_type NOT NULL,

    control_qubit INTEGER,

    target_qubit INTEGER NOT NULL
        CHECK (target_qubit >= 0),

    rotation_angle DOUBLE PRECISION,

    parameterized BOOLEAN NOT NULL DEFAULT FALSE,

    parameter_index INTEGER,

    CHECK (
        gate <> 'CNOT' OR control_qubit IS NOT NULL
    ),

    CHECK (
        control_qubit IS NULL OR control_qubit >= 0
    ),

    CHECK (
        control_qubit IS NULL OR
        control_qubit <> target_qubit
    ),

    CHECK (
        gate NOT IN ('RX', 'RY', 'RZ')
        OR rotation_angle IS NOT NULL
        OR parameterized
    ),

    CHECK (
        parameterized = FALSE OR parameter_index IS NOT NULL
    ),

    CHECK (
        parameter_index IS NULL OR parameter_index >= 0
    ),

    CHECK (
        rotation_angle IS NULL OR
        rotation_angle BETWEEN -1000000 AND 1000000
    ),

    UNIQUE(circuit_id, sequence_number)
);

CREATE INDEX idx_gates_circuit_sequence
    ON circuit_gates(circuit_id, sequence_number);

-- ------------------------------------------------------------
-- 6. Trainable parameters
-- ------------------------------------------------------------

CREATE TABLE circuit_parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id)
        ON DELETE CASCADE,

    parameter_index INTEGER NOT NULL
        CHECK (parameter_index >= 0),

    parameter_name VARCHAR(100) NOT NULL,

    initial_value DOUBLE PRECISION NOT NULL,

    current_value DOUBLE PRECISION NOT NULL,

    lower_bound DOUBLE PRECISION NOT NULL DEFAULT -6.283185307,

    upper_bound DOUBLE PRECISION NOT NULL DEFAULT 6.283185307,

    trainable BOOLEAN NOT NULL DEFAULT TRUE,

    CHECK (
        lower_bound <= upper_bound
    ),

    CHECK (
        current_value BETWEEN lower_bound AND upper_bound
    ),

    CHECK (
        initial_value BETWEEN lower_bound AND upper_bound
    ),

    UNIQUE(circuit_id, parameter_index),
    UNIQUE(circuit_id, parameter_name)
);

-- ------------------------------------------------------------
-- 7. Training datasets
-- ------------------------------------------------------------

CREATE TABLE training_datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    dataset_name VARCHAR(150) NOT NULL,

    dataset_version VARCHAR(50) NOT NULL,

    feature_count INTEGER NOT NULL
        CHECK (feature_count > 0),

    sample_count INTEGER NOT NULL
        CHECK (sample_count > 0),

    split_type VARCHAR(20) NOT NULL
        CHECK (split_type IN ('TRAIN', 'VALIDATION', 'TEST')),

    source_hash VARCHAR(128) NOT NULL,

    contains_sensitive_data BOOLEAN NOT NULL DEFAULT FALSE,

    preprocessing_description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(experiment_id, dataset_name, dataset_version, split_type)
);

CREATE INDEX idx_datasets_experiment
    ON training_datasets(experiment_id, split_type);

-- ------------------------------------------------------------
-- 8. Optimizer configurations
-- ------------------------------------------------------------

CREATE TABLE optimizer_configs (
    optimizer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    optimizer optimizer_type NOT NULL,

    learning_rate DOUBLE PRECISION NOT NULL
        CHECK (learning_rate > 0 AND learning_rate <= 1),

    maximum_epochs INTEGER NOT NULL
        CHECK (maximum_epochs > 0),

    batch_size INTEGER NOT NULL
        CHECK (batch_size > 0),

    convergence_threshold DOUBLE PRECISION NOT NULL
        CHECK (convergence_threshold >= 0),

    shots_per_measurement INTEGER NOT NULL DEFAULT 1000
        CHECK (shots_per_measurement > 0),

    gradient_method VARCHAR(40) NOT NULL
        CHECK (
            gradient_method IN (
                'PARAMETER_SHIFT',
                'FINITE_DIFFERENCE',
                'SPSA'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(optimizer_id, experiment_id)
);

-- ------------------------------------------------------------
-- 9. Observable definitions
-- ------------------------------------------------------------

CREATE TABLE observables (
    observable_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id),

    observable_name VARCHAR(100) NOT NULL,

    pauli_operator VARCHAR(20) NOT NULL,

    measured_qubit INTEGER NOT NULL
        CHECK (measured_qubit >= 0),

    coefficient DOUBLE PRECISION NOT NULL DEFAULT 1.0,

    UNIQUE(circuit_id, observable_name)
);

-- ------------------------------------------------------------
-- 10. Training runs
-- ------------------------------------------------------------

CREATE TABLE training_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),

    circuit_id BIGINT NOT NULL,

    optimizer_id BIGINT NOT NULL,

    dataset_id BIGINT NOT NULL
        REFERENCES training_datasets(dataset_id),

    status experiment_status NOT NULL DEFAULT 'CREATED',

    execution_environment VARCHAR(100) NOT NULL,

    hardware_backend VARCHAR(150),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(circuit_id, experiment_id)
        REFERENCES quantum_circuits(circuit_id, experiment_id),

    FOREIGN KEY(optimizer_id, experiment_id)
        REFERENCES optimizer_configs(optimizer_id, experiment_id),

    CHECK (
        completed_at IS NULL OR started_at IS NOT NULL
    ),

    CHECK (
        status <> 'COMPLETED' OR completed_at IS NOT NULL
    ),

    CHECK (
        status <> 'FAILED' OR failure_reason IS NOT NULL
    )
);

CREATE INDEX idx_training_runs_status
    ON training_runs(status, created_at DESC);

-- ------------------------------------------------------------
-- 11. Measurement records
-- ------------------------------------------------------------

CREATE TABLE quantum_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id)
        ON DELETE CASCADE,

    observable_id BIGINT NOT NULL
        REFERENCES observables(observable_id),

    epoch INTEGER NOT NULL
        CHECK (epoch >= 0),

    shots INTEGER NOT NULL
        CHECK (shots > 0),

    count_zero INTEGER NOT NULL DEFAULT 0
        CHECK (count_zero >= 0),

    count_one INTEGER NOT NULL DEFAULT 0
        CHECK (count_one >= 0),

    expectation_value DOUBLE PRECISION NOT NULL
        CHECK (expectation_value BETWEEN -1 AND 1),

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (count_zero + count_one = shots)
);

CREATE INDEX idx_measurements_run_epoch
    ON quantum_measurements(run_id, epoch);

-- ------------------------------------------------------------
-- 12. Training metrics
-- ------------------------------------------------------------

CREATE TABLE training_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id)
        ON DELETE CASCADE,

    epoch INTEGER NOT NULL
        CHECK (epoch > 0),

    training_loss DOUBLE PRECISION NOT NULL
        CHECK (training_loss >= 0),

    validation_loss DOUBLE PRECISION
        CHECK (
            validation_loss IS NULL OR validation_loss >= 0
        ),

    accuracy DOUBLE PRECISION
        CHECK (
            accuracy IS NULL OR accuracy BETWEEN 0 AND 1
        ),

    gradient_norm DOUBLE PRECISION
        CHECK (
            gradient_norm IS NULL OR gradient_norm >= 0
        ),

    execution_time_ms BIGINT
        CHECK (
            execution_time_ms IS NULL OR execution_time_ms >= 0
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(run_id, epoch)
);

CREATE INDEX idx_metrics_run_loss
    ON training_metrics(run_id, training_loss);

-- ------------------------------------------------------------
-- 13. Evaluation results
-- ------------------------------------------------------------

CREATE TABLE evaluation_results (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES training_runs(run_id),

    dataset_id BIGINT NOT NULL
        REFERENCES training_datasets(dataset_id),

    accuracy DOUBLE PRECISION
        CHECK (accuracy BETWEEN 0 AND 1),

    precision_score DOUBLE PRECISION
        CHECK (precision_score BETWEEN 0 AND 1),

    recall_score DOUBLE PRECISION
        CHECK (recall_score BETWEEN 0 AND 1),

    f1_score DOUBLE PRECISION
        CHECK (f1_score BETWEEN 0 AND 1),

    evaluation_loss DOUBLE PRECISION
        CHECK (evaluation_loss >= 0),

    evaluation_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(run_id, dataset_id)
);

-- ------------------------------------------------------------
-- 14. Validate gate-to-circuit relationships
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_circuit_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    configured_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO configured_qubits
    FROM quantum_circuits
    WHERE circuit_id = NEW.circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit does not exist.';
    END IF;

    IF NEW.target_qubit >= configured_qubits THEN
        RAISE EXCEPTION
            'Target qubit % exceeds circuit size %.',
            NEW.target_qubit,
            configured_qubits;
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND NEW.control_qubit >= configured_qubits THEN
        RAISE EXCEPTION
            'Control qubit exceeds circuit size.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_circuit_gate
BEFORE INSERT OR UPDATE ON circuit_gates
FOR EACH ROW
EXECUTE FUNCTION validate_circuit_gate();

-- ------------------------------------------------------------
-- 15. Validate observable qubit
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_observable_qubit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    configured_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO configured_qubits
    FROM quantum_circuits
    WHERE circuit_id = NEW.circuit_id;

    IF NEW.measured_qubit >= configured_qubits THEN
        RAISE EXCEPTION 'Observable references an invalid qubit.';
    END IF;

    IF length(NEW.pauli_operator) <> configured_qubits THEN
        RAISE EXCEPTION
            'Pauli operator length must equal circuit qubit count.';
    END IF;

    IF NEW.pauli_operator !~ '^[IXYZ]+$' THEN
        RAISE EXCEPTION 'Invalid Pauli operator.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_observable
BEFORE INSERT OR UPDATE ON observables
FOR EACH ROW
EXECUTE FUNCTION validate_observable_qubit();

-- ------------------------------------------------------------
-- 16. Validate experiment state transitions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'COMPLETED'
       AND NEW.status <> 'COMPLETED' THEN
        RAISE EXCEPTION
            'Completed experiments cannot be reopened or modified in status.';
    END IF;

    IF OLD.status = 'CANCELLED'
       AND NEW.status <> 'CANCELLED' THEN
        RAISE EXCEPTION
            'Cancelled experiments cannot transition.';
    END IF;

    IF OLD.status = 'FAILED'
       AND NEW.status NOT IN ('FAILED', 'VALIDATING') THEN
        RAISE EXCEPTION
            'Failed experiments must be revalidated before restarting.';
    END IF;

    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ------------------------------------------------------------
-- 17. Record training run transitions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_run_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'COMPLETED'
       AND NEW.status <> 'COMPLETED' THEN
        RAISE EXCEPTION 'Completed runs are immutable in status.';
    END IF;

    IF OLD.status = 'CANCELLED'
       AND NEW.status <> 'CANCELLED' THEN
        RAISE EXCEPTION 'Cancelled runs cannot restart.';
    END IF;

    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_run_transition
BEFORE UPDATE ON training_runs
FOR EACH ROW
EXECUTE FUNCTION enforce_run_transition();

-- ------------------------------------------------------------
-- 18. Eligibility determination
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_experiment_readiness(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    ready BOOLEAN,
    circuit_count BIGINT,
    dataset_count BIGINT,
    optimizer_count BIGINT,
    explanation TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        (
            COUNT(DISTINCT c.circuit_id) > 0
            AND COUNT(DISTINCT d.dataset_id) > 0
            AND COUNT(DISTINCT o.optimizer_id) > 0
        ) AS ready,

        COUNT(DISTINCT c.circuit_id),

        COUNT(DISTINCT d.dataset_id),

        COUNT(DISTINCT o.optimizer_id),

        CASE
            WHEN COUNT(DISTINCT c.circuit_id) = 0
                THEN 'No circuit configured'
            WHEN COUNT(DISTINCT d.dataset_id) = 0
                THEN 'No training dataset configured'
            WHEN COUNT(DISTINCT o.optimizer_id) = 0
                THEN 'No optimizer configured'
            ELSE 'Experiment configuration is complete'
        END

    FROM experiments e

    LEFT JOIN quantum_circuits c
        ON c.experiment_id = e.experiment_id
       AND c.status = 'VALIDATED'

    LEFT JOIN training_datasets d
        ON d.experiment_id = e.experiment_id
       AND d.split_type = 'TRAIN'

    LEFT JOIN optimizer_configs o
        ON o.experiment_id = e.experiment_id

    WHERE e.experiment_id = p_experiment_id
    GROUP BY e.experiment_id;
$$;

-- ------------------------------------------------------------
-- 19. Training metric reporting view
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW v_training_performance AS
SELECT
    r.run_id,
    r.experiment_id,
    r.status,
    c.circuit_name,
    c.architecture,
    d.dataset_name,
    o.optimizer,
    o.gradient_method,
    MAX(m.epoch) AS epochs_completed,
    MIN(m.training_loss) AS minimum_training_loss,
    AVG(m.accuracy) AS average_accuracy,
    MAX(m.accuracy) AS maximum_accuracy,
    SUM(m.execution_time_ms) AS total_execution_time_ms

FROM training_runs r

JOIN quantum_circuits c
    ON c.circuit_id = r.circuit_id

JOIN training_datasets d
    ON d.dataset_id = r.dataset_id

JOIN optimizer_configs o
    ON o.optimizer_id = r.optimizer_id

LEFT JOIN training_metrics m
    ON m.run_id = r.run_id

GROUP BY
    r.run_id,
    r.experiment_id,
    r.status,
    c.circuit_name,
    c.architecture,
    d.dataset_name,
    o.optimizer,
    o.gradient_method;

-- ------------------------------------------------------------
-- 20. Insert research project
-- ------------------------------------------------------------

INSERT INTO projects (
    project_name,
    research_area,
    description
)
VALUES (
    'Variational Quantum Learning Research',
    'Quantum Machine Learning',
    'Study of parameterized quantum circuits and quantum classifiers.'
);

-- ------------------------------------------------------------
-- 21. Insert experiment
-- ------------------------------------------------------------

INSERT INTO experiments (
    project_id,
    experiment_name,
    qubit_count,
    feature_count,
    target_variable,
    description
)
SELECT
    project_id,
    'Two Qubit Variational Classifier',
    2,
    2,
    'binary_class',
    'Angle encoding with trainable rotations and CNOT entanglement.'
FROM projects
WHERE project_name = 'Variational Quantum Learning Research';

-- ------------------------------------------------------------
-- 22. Insert quantum circuit
-- ------------------------------------------------------------

INSERT INTO quantum_circuits (
    experiment_id,
    circuit_name,
    architecture,
    status,
    qubit_count,
    circuit_depth,
    parameter_count,
    encoding,
    entanglement_strategy
)
SELECT
    experiment_id,
    'QNN_2Q_ANSATZ',
    'VARIATIONAL',
    'VALIDATED',
    2,
    6,
    4,
    'ANGLE',
    'CNOT'
FROM experiments
WHERE experiment_name = 'Two Qubit Variational Classifier';

-- ------------------------------------------------------------
-- 23. Insert circuit gates
-- ------------------------------------------------------------

INSERT INTO circuit_gates (
    circuit_id,
    sequence_number,
    gate,
    target_qubit,
    parameterized,
    parameter_index
)
SELECT
    circuit_id,
    sequence_number,
    gate,
    target_qubit,
    parameterized,
    parameter_index
FROM quantum_circuits c
CROSS JOIN (
    VALUES
        (1, 'RY'::gate_type, 0, TRUE,  NULL::INTEGER),
        (2, 'RY'::gate_type, 1, TRUE,  NULL::INTEGER),
        (3, 'RY'::gate_type, 0, TRUE,  0),
        (4, 'RY'::gate_type, 1, TRUE,  1),
        (5, 'CNOT'::gate_type, 1, FALSE, NULL::INTEGER),
        (6, 'RY'::gate_type, 0, TRUE,  2),
        (7, 'RY'::gate_type, 1, TRUE,  3)
) AS gates(sequence_number, gate, target_qubit, parameterized, parameter_index)
WHERE c.circuit_name = 'QNN_2Q_ANSATZ';

-- Correct the control qubit for the entangling gate.
UPDATE circuit_gates g
SET control_qubit = 0
FROM quantum_circuits c
WHERE g.circuit_id = c.circuit_id
  AND c.circuit_name = 'QNN_2Q_ANSATZ'
  AND g.gate = 'CNOT';

-- ------------------------------------------------------------
-- 24. Insert trainable parameters
-- ------------------------------------------------------------

INSERT INTO circuit_parameters (
    circuit_id,
    parameter_index,
    parameter_name,
    initial_value,
    current_value
)
SELECT
    circuit_id,
    parameter_index,
    parameter_name,
    initial_value,
    initial_value
FROM quantum_circuits c
CROSS JOIN (
    VALUES
        (0, 'theta_0', 0.2),
        (1, 'theta_1', -0.3),
        (2, 'theta_2', 0.4),
        (3, 'theta_3', 0.1)
) AS p(parameter_index, parameter_name, initial_value)
WHERE c.circuit_name = 'QNN_2Q_ANSATZ';

-- ------------------------------------------------------------
-- 25. Dataset records
-- ------------------------------------------------------------

INSERT INTO training_datasets (
    experiment_id,
    dataset_name,
    dataset_version,
    feature_count,
    sample_count,
    split_type,
    source_hash,
    preprocessing_description
)
SELECT
    experiment_id,
    'Synthetic Binary Dataset',
    '1.0',
    2,
    100,
    'TRAIN',
    'sha256:synthetic-training-v1',
    'Finite-valued normalized angle-encoding features.'
FROM experiments
WHERE experiment_name = 'Two Qubit Variational Classifier';

INSERT INTO training_datasets (
    experiment_id,
    dataset_name,
    dataset_version,
    feature_count,
    sample_count,
    split_type,
    source_hash,
    preprocessing_description
)
SELECT
    experiment_id,
    'Synthetic Binary Dataset',
    '1.0',
    2,
    30,
    'TEST',
    'sha256:synthetic-test-v1',
    'Independent held-out evaluation examples.'
FROM experiments
WHERE experiment_name = 'Two Qubit Variational Classifier';

-- ------------------------------------------------------------
-- 26. Optimizer configuration
-- ------------------------------------------------------------

INSERT INTO optimizer_configs (
    experiment_id,
    optimizer,
    learning_rate,
    maximum_epochs,
    batch_size,
    convergence_threshold,
    shots_per_measurement,
    gradient_method
)
SELECT
    experiment_id,
    'SGD',
    0.05,
    100,
    16,
    0.0000001,
    1000,
    'PARAMETER_SHIFT'
FROM experiments
WHERE experiment_name = 'Two Qubit Variational Classifier';

-- ------------------------------------------------------------
-- 27. Observable
-- ------------------------------------------------------------

INSERT INTO observables (
    circuit_id,
    observable_name,
    pauli_operator,
    measured_qubit,
    coefficient
)
SELECT
    circuit_id,
    'CLASSIFICATION_Z',
    'ZI',
    0,
    1.0
FROM quantum_circuits
WHERE circuit_name = 'QNN_2Q_ANSATZ';

-- ------------------------------------------------------------
-- 28. Create training run
-- ------------------------------------------------------------

INSERT INTO training_runs (
    experiment_id,
    circuit_id,
    optimizer_id,
    dataset_id,
    status,
    execution_environment,
    hardware_backend
)
SELECT
    e.experiment_id,
    c.circuit_id,
    o.optimizer_id,
    d.dataset_id,
    'CREATED',
    'STATE_VECTOR_SIMULATOR',
    'LOCAL_CPU'
FROM experiments e
JOIN quantum_circuits c
    ON c.experiment_id = e.experiment_id
JOIN optimizer_configs o
    ON o.experiment_id = e.experiment_id
JOIN training_datasets d
    ON d.experiment_id = e.experiment_id
WHERE e.experiment_name = 'Two Qubit Variational Classifier'
  AND d.split_type = 'TRAIN';

-- ------------------------------------------------------------
-- 29. Transactional workflow processing
-- ------------------------------------------------------------

DO $$
DECLARE
    selected_run BIGINT;
    selected_experiment BIGINT;
BEGIN
    SELECT run_id, experiment_id
    INTO selected_run, selected_experiment
    FROM training_runs
    WHERE status = 'CREATED'
    ORDER BY run_id
    LIMIT 1
    FOR UPDATE;

    IF selected_run IS NULL THEN
        RAISE EXCEPTION 'No available training run.';
    END IF;

    UPDATE experiments
    SET status = 'READY'
    WHERE experiment_id = selected_experiment
      AND status = 'CREATED';

    UPDATE training_runs
    SET status = 'RUNNING'
    WHERE run_id = selected_run
      AND status = 'CREATED';

    RAISE NOTICE 'Training run % started.', selected_run;
END;
$$;

-- ------------------------------------------------------------
-- 30. Insert illustrative training metrics
-- ------------------------------------------------------------

INSERT INTO training_metrics (
    run_id,
    epoch,
    training_loss,
    validation_loss,
    accuracy,
    gradient_norm,
    execution_time_ms
)
SELECT
    run_id,
    metric.epoch,
    metric.loss,
    metric.validation_loss,
    metric.accuracy,
    metric.gradient_norm,
    metric.execution_time
FROM training_runs r
CROSS JOIN (
    VALUES
        (1, 0.92, 1.01, 0.50, 0.85, 18::BIGINT),
        (10, 0.61, 0.69, 0.67, 0.52, 17::BIGINT),
        (20, 0.42, 0.49, 0.75, 0.34, 16::BIGINT),
        (30, 0.29, 0.36, 0.83, 0.21, 16::BIGINT),
        (40, 0.18, 0.27, 0.87, 0.13, 15::BIGINT),
        (50, 0.12, 0.22, 0.90, 0.08, 15::BIGINT)
) AS metric(
    epoch,
    loss,
    validation_loss,
    accuracy,
    gradient_norm,
    execution_time
)
WHERE r.status = 'RUNNING';

-- ------------------------------------------------------------
-- 31. Record measurement outcomes
-- ------------------------------------------------------------

INSERT INTO quantum_measurements (
    run_id,
    observable_id,
    epoch,
    shots,
    count_zero,
    count_one,
    expectation_value
)
SELECT
    r.run_id,
    o.observable_id,
    50,
    1000,
    900,
    100,
    0.8
FROM training_runs r
JOIN quantum_circuits c
    ON c.circuit_id = r.circuit_id
JOIN observables o
    ON o.circuit_id = c.circuit_id
WHERE r.status = 'RUNNING';

-- ------------------------------------------------------------
-- 32. Complete the training run
-- ------------------------------------------------------------

UPDATE training_runs
SET status = 'COMPLETED'
WHERE status = 'RUNNING';

-- ------------------------------------------------------------
-- 33. Update experiment status
-- ------------------------------------------------------------

UPDATE experiments e
SET status = 'COMPLETED'
WHERE e.status IN ('READY', 'RUNNING')
  AND EXISTS (
      SELECT 1
      FROM training_runs r
      WHERE r.experiment_id = e.experiment_id
        AND r.status = 'COMPLETED'
  );

-- ------------------------------------------------------------
-- 34. Evaluation records
-- ------------------------------------------------------------

INSERT INTO evaluation_results (
    run_id,
    dataset_id,
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    evaluation_loss
)
SELECT
    r.run_id,
    d.dataset_id,
    0.90,
    0.89,
    0.91,
    0.90,
    0.18
FROM training_runs r
JOIN training_datasets d
    ON d.experiment_id = r.experiment_id
WHERE r.status = 'COMPLETED'
  AND d.split_type = 'TEST';

-- ------------------------------------------------------------
-- 35. Retrieval: experiment inventory
-- ------------------------------------------------------------

SELECT
    p.project_name,
    e.experiment_name,
    e.status,
    e.qubit_count,
    e.feature_count,
    e.created_at
FROM projects p
JOIN experiments e
    ON e.project_id = p.project_id
ORDER BY e.created_at DESC;

-- ------------------------------------------------------------
-- 36. Validation: experiment readiness
-- ------------------------------------------------------------

SELECT *
FROM check_experiment_readiness(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_name = 'Two Qubit Variational Classifier'
    )
);

-- ------------------------------------------------------------
-- 37. Circuit architecture retrieval
-- ------------------------------------------------------------

SELECT
    c.circuit_name,
    c.architecture,
    c.encoding,
    c.qubit_count,
    c.circuit_depth,
    g.sequence_number,
    g.gate,
    g.control_qubit,
    g.target_qubit,
    g.parameterized
FROM quantum_circuits c
JOIN circuit_gates g
    ON g.circuit_id = c.circuit_id
ORDER BY c.circuit_id, g.sequence_number;

-- ------------------------------------------------------------
-- 38. Parameter evaluation
-- ------------------------------------------------------------

SELECT
    c.circuit_name,
    p.parameter_name,
    p.initial_value,
    p.current_value,
    p.trainable,
    p.lower_bound,
    p.upper_bound
FROM circuit_parameters p
JOIN quantum_circuits c
    ON c.circuit_id = p.circuit_id
ORDER BY p.parameter_index;

-- ------------------------------------------------------------
-- 39. Aggregated training metrics
-- ------------------------------------------------------------

SELECT
    run_id,
    COUNT(*) AS recorded_epochs,
    MIN(training_loss) AS best_training_loss,
    AVG(training_loss) AS mean_training_loss,
    MAX(accuracy) AS best_accuracy,
    AVG(execution_time_ms) AS mean_epoch_time_ms
FROM training_metrics
GROUP BY run_id
ORDER BY run_id;

-- ------------------------------------------------------------
-- 40. Evaluation reporting
-- ------------------------------------------------------------

SELECT
    r.run_id,
    e.experiment_name,
    d.split_type,
    er.accuracy,
    er.precision_score,
    er.recall_score,
    er.f1_score,
    er.evaluation_loss
FROM evaluation_results er
JOIN training_runs r
    ON r.run_id = er.run_id
JOIN experiments e
    ON e.experiment_id = r.experiment_id
JOIN training_datasets d
    ON d.dataset_id = er.dataset_id;

-- ------------------------------------------------------------
-- 41. Measurement reporting
-- ------------------------------------------------------------

SELECT
    run_id,
    epoch,
    SUM(shots) AS total_shots,
    SUM(count_zero) AS zero_count,
    SUM(count_one) AS one_count,
    AVG(expectation_value) AS average_expectation
FROM quantum_measurements
GROUP BY run_id, epoch
ORDER BY run_id, epoch;

-- ------------------------------------------------------------
-- 42. Training performance view
-- ------------------------------------------------------------

SELECT *
FROM v_training_performance
ORDER BY run_id;

-- ------------------------------------------------------------
-- 43. Failure-case validation
-- ------------------------------------------------------------

-- The following block intentionally demonstrates rejection
-- of a gate that references a nonexistent qubit.

DO $$
DECLARE
    selected_circuit BIGINT;
BEGIN
    SELECT circuit_id
    INTO selected_circuit
    FROM quantum_circuits
    WHERE circuit_name = 'QNN_2Q_ANSATZ';

    BEGIN
        INSERT INTO circuit_gates (
            circuit_id,
            sequence_number,
            gate,
            target_qubit
        )
        VALUES (
            selected_circuit,
            100,
            'RY',
            5
        );

        RAISE EXCEPTION
            'Validation failure: invalid gate was accepted.';

    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid gate rejected by constraint.';
        WHEN raise_exception THEN
            IF SQLERRM LIKE 'Target qubit%' THEN
                RAISE NOTICE 'Invalid gate rejected by trigger.';
            ELSE
                RAISE;
            END IF;
    END;
END;
$$;

-- ------------------------------------------------------------
-- 44. Demonstrate transactional rollback
-- ------------------------------------------------------------

DO $$
DECLARE
    initial_count BIGINT;
    final_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO initial_count
    FROM circuit_parameters;

    BEGIN
        INSERT INTO circuit_parameters (
            circuit_id,
            parameter_index,
            parameter_name,
            initial_value,
            current_value
        )
        SELECT
            circuit_id,
            999,
            'INVALID_PARAMETER',
            0,
            0
        FROM quantum_circuits
        WHERE circuit_name = 'QNN_2Q_ANSATZ';

        RAISE EXCEPTION 'Intentional rollback demonstration.';
    EXCEPTION
        WHEN raise_exception THEN
            RAISE NOTICE 'Transaction savepoint rolled back.';
    END;

    SELECT COUNT(*)
    INTO final_count
    FROM circuit_parameters;

    IF initial_count <> final_count THEN
        RAISE EXCEPTION 'Rollback integrity check failed.';
    END IF;

    RAISE NOTICE 'Parameter table integrity preserved.';
END;
$$;

COMMIT;
