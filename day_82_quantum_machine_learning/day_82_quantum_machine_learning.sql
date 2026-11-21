/*
 * ============================================================
 * QUANTUM MACHINE LEARNING
 * QML LANDSCAPE AND EXPERIMENT GOVERNANCE DATABASE
 * PostgreSQL 15+
 * ============================================================
 *
 * Relational model:
 *
 * Organizations
 *   -> Repositories of research experiments
 *   -> Datasets
 *   -> Quantum backends
 *   -> Algorithm definitions
 *   -> Circuit configurations
 *   -> Experiments
 *   -> Experiment executions
 *   -> Evaluation metrics
 *   -> Governance decisions
 *
 * Distinguishes:
 * - Quantum algorithm selection
 * - Classical versus quantum-inspired methods
 * - Quantum hardware capabilities
 * - Circuit resource requirements
 * - Data governance
 * - Experiment lifecycle
 * - Execution outcomes
 * - Evaluation measurements
 *
 * All examples use synthetic research data.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS qml;

SET search_path TO qml, public;

-- ============================================================
-- 1. ENUM TYPES
-- ============================================================

CREATE TYPE algorithm_family AS ENUM (
    'VARIATIONAL_CLASSIFIER',
    'QUANTUM_NEURAL_NETWORK',
    'QUANTUM_KERNEL',
    'QUANTUM_GENERATIVE',
    'QUANTUM_REINFORCEMENT',
    'VQE',
    'QAOA',
    'QUANTUM_INSPIRED'
);

CREATE TYPE backend_type AS ENUM (
    'STATEVECTOR',
    'SHOT_BASED',
    'NOISY_SIMULATOR',
    'QUANTUM_HARDWARE'
);

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATED',
    'APPROVED',
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'REJECTED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE data_classification AS ENUM (
    'PUBLIC',
    'INTERNAL',
    'CONFIDENTIAL',
    'RESTRICTED'
);

CREATE TYPE governance_status AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);

CREATE TYPE workload_category AS ENUM (
    'SUPERVISED_LEARNING',
    'SIMILARITY_LEARNING',
    'OPTIMIZATION',
    'CHEMISTRY',
    'GENERATIVE',
    'REINFORCEMENT'
);

-- ============================================================
-- 2. ORGANIZATIONS AND RESEARCH USERS
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE research_users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(40) NOT NULL CHECK (
        role IN (
            'RESEARCHER',
            'PRINCIPAL_INVESTIGATOR',
            'DATA_STEWARD',
            'GOVERNANCE_OFFICER',
            'ADMINISTRATOR'
        )
    ),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_research_users_organization
    ON research_users(organization_id, role);

-- ============================================================
-- 3. QML ALGORITHM CATALOG
-- ============================================================

CREATE TABLE algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    algorithm_code VARCHAR(60) NOT NULL UNIQUE,
    algorithm_name VARCHAR(150) NOT NULL,
    family algorithm_family NOT NULL,
    description TEXT NOT NULL,
    hybrid_classical_quantum BOOLEAN NOT NULL DEFAULT TRUE,
    requires_trainable_parameters BOOLEAN NOT NULL DEFAULT FALSE,
    typical_applications TEXT[],
    limitations TEXT[],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO algorithms (
    algorithm_code,
    algorithm_name,
    family,
    description,
    hybrid_classical_quantum,
    requires_trainable_parameters,
    typical_applications,
    limitations
)
VALUES
(
    'VQC',
    'Variational Quantum Classifier',
    'VARIATIONAL_CLASSIFIER',
    'Parameterized quantum circuit trained using a classical optimizer.',
    TRUE,
    TRUE,
    ARRAY['Classification', 'Pattern recognition'],
    ARRAY['Barren plateaus', 'Measurement overhead', 'Noise']
),
(
    'QNN',
    'Quantum Neural Network',
    'QUANTUM_NEURAL_NETWORK',
    'Quantum circuit layers integrated into trainable learning architectures.',
    TRUE,
    TRUE,
    ARRAY['Feature learning', 'Hybrid neural models'],
    ARRAY['Limited hardware scale', 'Training difficulty']
),
(
    'QKERNEL',
    'Quantum Kernel Learning',
    'QUANTUM_KERNEL',
    'Quantum feature maps produce fidelity-based similarity matrices.',
    TRUE,
    FALSE,
    ARRAY['Classification', 'Similarity learning'],
    ARRAY['Kernel estimation cost', 'Quadratic matrix storage']
),
(
    'QGEN',
    'Quantum Generative Model',
    'QUANTUM_GENERATIVE',
    'Parameterized quantum circuits generate probability distributions.',
    TRUE,
    TRUE,
    ARRAY['Generative modeling', 'Distribution learning'],
    ARRAY['Sampling overhead', 'Optimization complexity']
),
(
    'QRL',
    'Quantum Reinforcement Learning',
    'QUANTUM_REINFORCEMENT',
    'Quantum parameterized policies and value representations.',
    TRUE,
    TRUE,
    ARRAY['Sequential decision making'],
    ARRAY['Reward estimation', 'Sampling cost']
),
(
    'VQE',
    'Variational Quantum Eigensolver',
    'VQE',
    'Hybrid quantum-classical estimation of ground-state energies.',
    TRUE,
    TRUE,
    ARRAY['Quantum chemistry', 'Molecular energy'],
    ARRAY['Measurement cost', 'Noise sensitivity']
),
(
    'QAOA',
    'Quantum Approximate Optimization Algorithm',
    'QAOA',
    'Alternating parameterized circuits for combinatorial optimization.',
    TRUE,
    TRUE,
    ARRAY['Combinatorial optimization'],
    ARRAY['Circuit depth', 'Optimization landscape']
),
(
    'QINSPIRED',
    'Quantum-Inspired Classical Algorithms',
    'QUANTUM_INSPIRED',
    'Classical algorithms motivated by quantum computational techniques.',
    FALSE,
    FALSE,
    ARRAY['Optimization', 'Tensor networks'],
    ARRAY['Does not perform quantum computation']
);

-- ============================================================
-- 4. DATASETS AND DATA GOVERNANCE
-- ============================================================

CREATE TABLE datasets (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    owner_user_id BIGINT NOT NULL
        REFERENCES research_users(user_id),
    dataset_name VARCHAR(180) NOT NULL,
    sample_count BIGINT NOT NULL CHECK (sample_count > 0),
    feature_count INTEGER NOT NULL CHECK (feature_count > 0),
    classification data_classification NOT NULL,
    consent_verified BOOLEAN NOT NULL DEFAULT FALSE,
    provenance_verified BOOLEAN NOT NULL DEFAULT FALSE,
    preprocessing_description TEXT,
    checksum_sha256 CHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(organization_id, dataset_name),
    CHECK (
        checksum_sha256 IS NULL OR
        checksum_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE INDEX idx_datasets_classification
    ON datasets(classification, organization_id);

CREATE TABLE dataset_governance (
    governance_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    dataset_id BIGINT NOT NULL REFERENCES datasets(dataset_id),
    reviewer_id BIGINT NOT NULL REFERENCES research_users(user_id),
    status governance_status NOT NULL DEFAULT 'PENDING',
    decision_reason TEXT,
    reviewed_at TIMESTAMPTZ,
    UNIQUE(dataset_id, reviewer_id),
    CHECK (
        (status = 'PENDING' AND reviewed_at IS NULL)
        OR
        (status <> 'PENDING' AND reviewed_at IS NOT NULL)
    )
);

-- ============================================================
-- 5. QUANTUM BACKENDS
-- ============================================================

CREATE TABLE quantum_backends (
    backend_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    backend_name VARCHAR(150) NOT NULL UNIQUE,
    backend backend_type NOT NULL,
    provider_name VARCHAR(150),
    maximum_qubits INTEGER NOT NULL CHECK (maximum_qubits > 0),
    maximum_circuit_depth INTEGER NOT NULL CHECK (
        maximum_circuit_depth > 0
    ),
    maximum_shots INTEGER NOT NULL CHECK (maximum_shots > 0),
    gate_fidelity NUMERIC(10, 8) NOT NULL CHECK (
        gate_fidelity > 0 AND gate_fidelity <= 1
    ),
    measurement_fidelity NUMERIC(10, 8) NOT NULL CHECK (
        measurement_fidelity > 0 AND measurement_fidelity <= 1
    ),
    supports_entanglement BOOLEAN NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    hardware_region VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO quantum_backends (
    backend_name,
    backend,
    provider_name,
    maximum_qubits,
    maximum_circuit_depth,
    maximum_shots,
    gate_fidelity,
    measurement_fidelity,
    supports_entanglement,
    enabled,
    hardware_region
)
VALUES
(
    'Local Statevector Simulator',
    'STATEVECTOR',
    'Internal Research Infrastructure',
    24,
    1000,
    1000000,
    1.00000000,
    1.00000000,
    TRUE,
    TRUE,
    'LOCAL'
),
(
    'Shot Based Simulator',
    'SHOT_BASED',
    'Internal Research Infrastructure',
    30,
    500,
    100000,
    0.99900000,
    0.99900000,
    TRUE,
    TRUE,
    'LOCAL'
),
(
    'Noisy Simulation Backend',
    'NOISY_SIMULATOR',
    'Internal Research Infrastructure',
    20,
    200,
    50000,
    0.99500000,
    0.99000000,
    TRUE,
    TRUE,
    'LOCAL'
),
(
    'Approved Quantum Hardware',
    'QUANTUM_HARDWARE',
    'Research Hardware Provider',
    16,
    100,
    50000,
    0.99900000,
    0.99500000,
    TRUE,
    TRUE,
    'APPROVED_REGION'
);

CREATE INDEX idx_backends_type_enabled
    ON quantum_backends(backend, enabled);

-- ============================================================
-- 6. QUANTUM CIRCUIT DEFINITIONS
-- ============================================================

CREATE TABLE quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    circuit_name VARCHAR(180) NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (
        qubit_count BETWEEN 1 AND 1000
    ),
    circuit_depth INTEGER NOT NULL CHECK (circuit_depth > 0),
    trainable_parameters INTEGER NOT NULL DEFAULT 0 CHECK (
        trainable_parameters >= 0
    ),
    encoding_method VARCHAR(80) NOT NULL CHECK (
        encoding_method IN (
            'ANGLE_ENCODING',
            'AMPLITUDE_ENCODING',
            'BASIS_ENCODING',
            'IQP_ENCODING',
            'PRODUCT_ENCODING'
        )
    ),
    entanglement_method VARCHAR(80),
    measurement_method VARCHAR(80) NOT NULL,
    uses_entanglement BOOLEAN NOT NULL DEFAULT FALSE,
    circuit_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_circuits_qubits_depth
    ON quantum_circuits(qubit_count, circuit_depth);

-- ============================================================
-- 7. EXPERIMENTS
-- ============================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    experiment_code VARCHAR(80) NOT NULL UNIQUE,
    experiment_name VARCHAR(200) NOT NULL,
    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),
    researcher_id BIGINT NOT NULL
        REFERENCES research_users(user_id),
    algorithm_id BIGINT NOT NULL
        REFERENCES algorithms(algorithm_id),
    dataset_id BIGINT NOT NULL
        REFERENCES datasets(dataset_id),
    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id),
    backend_id BIGINT NOT NULL
        REFERENCES quantum_backends(backend_id),
    shots INTEGER NOT NULL CHECK (shots > 0),
    learning_rate NUMERIC(12, 8) CHECK (
        learning_rate IS NULL OR learning_rate > 0
    ),
    minimum_fidelity NUMERIC(10, 8) NOT NULL DEFAULT 0.5 CHECK (
        minimum_fidelity BETWEEN 0 AND 1
    ),
    status experiment_status NOT NULL DEFAULT 'CREATED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_experiments_status_created
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_researcher
    ON experiments(researcher_id, created_at DESC);

CREATE INDEX idx_experiments_algorithm
    ON experiments(algorithm_id, status);

-- ============================================================
-- 8. APPROVAL AND GOVERNANCE DECISIONS
-- ============================================================

CREATE TABLE experiment_approvals (
    approval_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),
    approver_id BIGINT NOT NULL
        REFERENCES research_users(user_id),
    decision governance_status NOT NULL,
    decision_reason TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(experiment_id, approver_id)
);

CREATE INDEX idx_experiment_approvals_decision
    ON experiment_approvals(experiment_id, decision);

-- ============================================================
-- 9. EXECUTION RECORDS
-- ============================================================

CREATE TABLE experiment_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),
    run_number INTEGER NOT NULL CHECK (run_number > 0),
    execution_status experiment_status NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    random_seed BIGINT,
    error_message TEXT,
    worker_identifier VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(experiment_id, run_number),
    CHECK (
        completed_at IS NULL OR
        started_at IS NOT NULL
    ),
    CHECK (
        completed_at IS NULL OR
        completed_at >= started_at
    )
);

CREATE INDEX idx_experiment_runs_status
    ON experiment_runs(execution_status, created_at DESC);

CREATE INDEX idx_experiment_runs_experiment
    ON experiment_runs(experiment_id, run_number DESC);

-- ============================================================
-- 10. EVALUATION METRICS
-- ============================================================

CREATE TABLE evaluation_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    run_id BIGINT NOT NULL UNIQUE
        REFERENCES experiment_runs(run_id),
    accuracy NUMERIC(12, 8) CHECK (
        accuracy BETWEEN 0 AND 1
    ),
    precision_score NUMERIC(12, 8) CHECK (
        precision_score BETWEEN 0 AND 1
    ),
    recall_score NUMERIC(12, 8) CHECK (
        recall_score BETWEEN 0 AND 1
    ),
    f1_score NUMERIC(12, 8) CHECK (
        f1_score BETWEEN 0 AND 1
    ),
    training_loss NUMERIC(18, 10) CHECK (
        training_loss >= 0
    ),
    validation_loss NUMERIC(18, 10) CHECK (
        validation_loss >= 0
    ),
    measurement_standard_error NUMERIC(18, 12) CHECK (
        measurement_standard_error >= 0
    ),
    execution_duration_ms BIGINT CHECK (
        execution_duration_ms >= 0
    ),
    shots_used BIGINT CHECK (shots_used > 0),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metrics_accuracy
    ON evaluation_metrics(accuracy DESC NULLS LAST);

-- ============================================================
-- 11. EXPERIMENT AUDIT LOG
-- ============================================================

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id),
    actor_id BIGINT REFERENCES research_users(user_id),
    action VARCHAR(80) NOT NULL,
    previous_status experiment_status,
    new_status experiment_status,
    detail TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_experiment_time
    ON experiment_audit(experiment_id, occurred_at DESC);

-- ============================================================
-- 12. VALIDATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_experiment(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    valid BOOLEAN,
    validation_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    e RECORD;
    failure_messages TEXT[] := ARRAY[]::TEXT[];
    estimated_fidelity NUMERIC;
    required_approvals INTEGER;
    actual_approvals INTEGER;
BEGIN
    SELECT
        x.*,
        d.classification,
        d.consent_verified,
        d.provenance_verified,
        c.qubit_count,
        c.circuit_depth,
        c.uses_entanglement,
        b.backend,
        b.maximum_qubits,
        b.maximum_circuit_depth,
        b.maximum_shots,
        b.gate_fidelity,
        b.measurement_fidelity,
        b.supports_entanglement,
        b.enabled
    INTO e
    FROM experiments x
    JOIN datasets d ON d.dataset_id = x.dataset_id
    JOIN quantum_circuits c ON c.circuit_id = x.circuit_id
    JOIN quantum_backends b ON b.backend_id = x.backend_id
    WHERE x.experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Experiment not found';
        RETURN;
    END IF;

    IF NOT e.provenance_verified THEN
        failure_messages := array_append(
            failure_messages,
            'Dataset provenance is not verified'
        );
    END IF;

    IF e.classification <> 'PUBLIC'
       AND NOT e.consent_verified THEN
        failure_messages := array_append(
            failure_messages,
            'Dataset consent is not verified'
        );
    END IF;

    IF e.classification = 'RESTRICTED'
       AND e.backend = 'QUANTUM_HARDWARE' THEN
        failure_messages := array_append(
            failure_messages,
            'Restricted dataset cannot use external hardware'
        );
    END IF;

    IF NOT e.enabled THEN
        failure_messages := array_append(
            failure_messages,
            'Backend is disabled'
        );
    END IF;

    IF e.qubit_count > e.maximum_qubits THEN
        failure_messages := array_append(
            failure_messages,
            'Qubit capacity exceeded'
        );
    END IF;

    IF e.circuit_depth > e.maximum_circuit_depth THEN
        failure_messages := array_append(
            failure_messages,
            'Circuit depth exceeded'
        );
    END IF;

    IF e.shots > e.maximum_shots THEN
        failure_messages := array_append(
            failure_messages,
            'Shot capacity exceeded'
        );
    END IF;

    IF e.uses_entanglement AND NOT e.supports_entanglement THEN
        failure_messages := array_append(
            failure_messages,
            'Backend does not support entanglement'
        );
    END IF;

    estimated_fidelity := POWER(
        e.gate_fidelity,
        e.qubit_count * e.circuit_depth
    ) * e.measurement_fidelity;

    IF estimated_fidelity < e.minimum_fidelity THEN
        failure_messages := array_append(
            failure_messages,
            'Estimated fidelity below minimum threshold'
        );
    END IF;

    SELECT COUNT(*)
    INTO required_approvals
    FROM research_users
    WHERE organization_id = e.organization_id
      AND role IN (
          'PRINCIPAL_INVESTIGATOR',
          'GOVERNANCE_OFFICER'
      )
      AND active = TRUE;

    SELECT COUNT(DISTINCT a.approver_id)
    INTO actual_approvals
    FROM experiment_approvals a
    JOIN research_users u ON u.user_id = a.approver_id
    WHERE a.experiment_id = p_experiment_id
      AND a.decision = 'APPROVED'
      AND u.active = TRUE
      AND u.organization_id = e.organization_id
      AND u.role IN (
          'PRINCIPAL_INVESTIGATOR',
          'GOVERNANCE_OFFICER'
      );

    IF actual_approvals < 1 THEN
        failure_messages := array_append(
            failure_messages,
            'At least one eligible governance approval is required'
        );
    END IF;

    IF array_length(failure_messages, 1) IS NULL THEN
        RETURN QUERY SELECT TRUE, 'All validation conditions passed';
    ELSE
        RETURN QUERY
        SELECT FALSE, array_to_string(failure_messages, '; ');
    END IF;
END;
$$;

-- ============================================================
-- 13. STATUS TRANSITION TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'CREATED' AND NEW.status IN (
            'VALIDATED', 'REJECTED', 'CANCELLED'
        ))
        OR
        (OLD.status = 'VALIDATED' AND NEW.status IN (
            'APPROVED', 'REJECTED', 'CANCELLED'
        ))
        OR
        (OLD.status = 'APPROVED' AND NEW.status IN (
            'QUEUED', 'CANCELLED'
        ))
        OR
        (OLD.status = 'QUEUED' AND NEW.status IN (
            'RUNNING', 'CANCELLED'
        ))
        OR
        (OLD.status = 'RUNNING' AND NEW.status IN (
            'COMPLETED', 'FAILED', 'CANCELLED'
        ))
    ) THEN
        RAISE EXCEPTION
            'Invalid experiment transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    NEW.updated_at = NOW();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ============================================================
-- 14. AUDIT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION audit_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO experiment_audit (
        experiment_id,
        action,
        previous_status,
        new_status,
        detail
    )
    VALUES (
        NEW.experiment_id,
        'STATUS_CHANGED',
        OLD.status,
        NEW.status,
        'Experiment lifecycle transition'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_audit
AFTER UPDATE OF status ON experiments
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION audit_experiment_status();

-- ============================================================
-- 15. ELIGIBILITY VIEW
-- ============================================================

CREATE OR REPLACE VIEW experiment_eligibility AS
SELECT
    e.experiment_id,
    e.experiment_code,
    e.experiment_name,
    a.algorithm_name,
    a.family,
    b.backend_name,
    b.backend,
    c.qubit_count,
    c.circuit_depth,
    e.shots,
    e.status,
    d.dataset_name,
    d.classification,
    ROUND(
        (
            POWER(
                b.gate_fidelity,
                c.qubit_count * c.circuit_depth
            ) * b.measurement_fidelity
        )::NUMERIC,
        8
    ) AS estimated_fidelity,
    e.minimum_fidelity,
    CASE
        WHEN NOT b.enabled THEN FALSE
        WHEN c.qubit_count > b.maximum_qubits THEN FALSE
        WHEN c.circuit_depth > b.maximum_circuit_depth THEN FALSE
        WHEN e.shots > b.maximum_shots THEN FALSE
        WHEN NOT d.provenance_verified THEN FALSE
        WHEN d.classification <> 'PUBLIC'
             AND NOT d.consent_verified THEN FALSE
        WHEN d.classification = 'RESTRICTED'
             AND b.backend = 'QUANTUM_HARDWARE' THEN FALSE
        WHEN c.uses_entanglement AND NOT b.supports_entanglement THEN FALSE
        WHEN POWER(
            b.gate_fidelity,
            c.qubit_count * c.circuit_depth
        ) * b.measurement_fidelity < e.minimum_fidelity THEN FALSE
        ELSE TRUE
    END AS technically_eligible
FROM experiments e
JOIN algorithms a ON a.algorithm_id = e.algorithm_id
JOIN datasets d ON d.dataset_id = e.dataset_id
JOIN quantum_circuits c ON c.circuit_id = e.circuit_id
JOIN quantum_backends b ON b.backend_id = e.backend_id;

-- ============================================================
-- 16. RESOURCE ESTIMATION FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION estimate_circuit_resources(
    p_qubits INTEGER,
    p_depth INTEGER,
    p_shots INTEGER
)
RETURNS TABLE (
    statevector_amplitudes NUMERIC,
    statevector_memory_bytes NUMERIC,
    approximate_gate_operations NUMERIC,
    approximate_measurement_operations NUMERIC
)
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
    IF p_qubits < 1 OR p_qubits > 1000
       OR p_depth < 1 OR p_shots < 1 THEN
        RAISE EXCEPTION 'Invalid resource estimation parameters';
    END IF;

    RETURN QUERY
    SELECT
        POWER(2::NUMERIC, p_qubits),
        POWER(2::NUMERIC, p_qubits) * 16,
        p_depth::NUMERIC * p_qubits,
        p_shots::NUMERIC * p_qubits;
END;
$$;

-- ============================================================
-- 17. ORGANIZATION AND USERS
-- ============================================================

INSERT INTO organizations(organization_name)
VALUES
('Quantum Research Laboratory'),
('Applied Computing Research Unit');

INSERT INTO research_users (
    organization_id,
    username,
    email,
    role
)
VALUES
(1, 'researcher01', 'researcher01@example.org', 'RESEARCHER'),
(1, 'principal01', 'principal01@example.org', 'PRINCIPAL_INVESTIGATOR'),
(1, 'governance01', 'governance01@example.org', 'GOVERNANCE_OFFICER'),
(1, 'steward01', 'steward01@example.org', 'DATA_STEWARD'),
(2, 'researcher02', 'researcher02@example.org', 'RESEARCHER');

-- ============================================================
-- 18. SAMPLE DATASETS
-- ============================================================

INSERT INTO datasets (
    organization_id,
    owner_user_id,
    dataset_name,
    sample_count,
    feature_count,
    classification,
    consent_verified,
    provenance_verified,
    checksum_sha256
)
VALUES
(
    1, 1,
    'Synthetic Binary Classification',
    1000, 4, 'PUBLIC',
    TRUE, TRUE,
    REPEAT('a', 64)
),
(
    1, 1,
    'Restricted Experimental Dataset',
    500, 4, 'RESTRICTED',
    TRUE, TRUE,
    REPEAT('b', 64)
),
(
    1, 1,
    'Unverified Provenance Dataset',
    250, 3, 'INTERNAL',
    TRUE, FALSE,
    REPEAT('c', 64)
);

INSERT INTO dataset_governance (
    dataset_id,
    reviewer_id,
    status,
    decision_reason,
    reviewed_at
)
VALUES
(1, 4, 'APPROVED', 'Synthetic data provenance verified.', NOW());

-- ============================================================
-- 19. SAMPLE CIRCUITS
-- ============================================================

INSERT INTO quantum_circuits (
    circuit_name,
    qubit_count,
    circuit_depth,
    trainable_parameters,
    encoding_method,
    entanglement_method,
    measurement_method,
    uses_entanglement
)
VALUES
(
    'Two Qubit Variational Circuit',
    2, 8, 4,
    'ANGLE_ENCODING',
    'CNOT',
    'PAULI_Z',
    TRUE
),
(
    'Quantum Kernel Feature Map',
    4, 12, 0,
    'IQP_ENCODING',
    'CNOT',
    'COMPUTATIONAL_BASIS',
    TRUE
),
(
    'Restricted Deep Circuit',
    20, 250, 40,
    'AMPLITUDE_ENCODING',
    'CNOT',
    'PAULI_Z',
    TRUE
);

-- ============================================================
-- 20. SAMPLE EXPERIMENTS
-- ============================================================

INSERT INTO experiments (
    experiment_code,
    experiment_name,
    organization_id,
    researcher_id,
    algorithm_id,
    dataset_id,
    circuit_id,
    backend_id,
    shots,
    learning_rate,
    minimum_fidelity
)
VALUES
(
    'QML-001',
    'Hybrid Variational Classification',
    1, 1, 1, 1, 1, 4,
    2048, 0.01, 0.80
),
(
    'QML-002',
    'Quantum Kernel Similarity Analysis',
    1, 1, 3, 1, 2, 2,
    4096, NULL, 0.75
),
(
    'QML-003',
    'Restricted Hardware Experiment',
    1, 1, 1, 2, 1, 4,
    1024, 0.01, 0.70
),
(
    'QML-004',
    'Unverified Dataset Experiment',
    1, 1, 1, 3, 1, 1,
    1024, 0.01, 0.70
),
(
    'QML-005',
    'Deep Circuit Capacity Test',
    1, 1, 2, 1, 3, 4,
    1024, 0.01, 0.50
);

-- ============================================================
-- 21. GOVERNANCE APPROVALS
-- ============================================================

INSERT INTO experiment_approvals (
    experiment_id,
    approver_id,
    decision,
    decision_reason
)
VALUES
(
    1, 2, 'APPROVED',
    'Research design and methodology reviewed.'
),
(
    2, 2, 'APPROVED',
    'Kernel experiment approved.'
),
(
    3, 2, 'APPROVED',
    'Administrative approval recorded.'
),
(
    4, 2, 'APPROVED',
    'Approval does not override dataset validation.'
);

-- ============================================================
-- 22. EXPERIMENT VALIDATION
-- ============================================================

SELECT
    e.experiment_code,
    v.valid,
    v.validation_message
FROM experiments e
CROSS JOIN LATERAL validate_experiment(e.experiment_id) v
ORDER BY e.experiment_id;

-- ============================================================
-- 23. APPROVAL VALIDATION
-- ============================================================

SELECT
    e.experiment_code,
    a.username AS approver,
    a.role,
    ea.decision,
    ea.decision_reason,
    ea.decided_at
FROM experiment_approvals ea
JOIN experiments e ON e.experiment_id = ea.experiment_id
JOIN research_users a ON a.user_id = ea.approver_id
ORDER BY ea.experiment_id, ea.decided_at;

-- ============================================================
-- 24. ELIGIBILITY REPORT
-- ============================================================

SELECT
    experiment_code,
    algorithm_name,
    backend_name,
    qubit_count,
    circuit_depth,
    shots,
    estimated_fidelity,
    technically_eligible,
    status
FROM experiment_eligibility
ORDER BY experiment_id;

-- ============================================================
-- 25. RESOURCE ESTIMATION
-- ============================================================

SELECT *
FROM estimate_circuit_resources(4, 12, 2048);

-- ============================================================
-- 26. ALGORITHM LANDSCAPE REPORT
-- ============================================================

SELECT
    family,
    COUNT(*) AS algorithm_count,
    STRING_AGG(algorithm_name, ', ' ORDER BY algorithm_name)
        AS available_algorithms,
    BOOL_OR(hybrid_classical_quantum)
        AS includes_hybrid_methods
FROM algorithms
GROUP BY family
ORDER BY family;

-- ============================================================
-- 27. ELIGIBILITY AND EXPERIMENT AGGREGATION
-- ============================================================

SELECT
    a.family,
    b.backend,
    COUNT(*) AS experiment_count,
    COUNT(*) FILTER (
        WHERE ee.technically_eligible
    ) AS eligible_experiments,
    COUNT(*) FILTER (
        WHERE NOT ee.technically_eligible
    ) AS ineligible_experiments
FROM experiments e
JOIN algorithms a ON a.algorithm_id = e.algorithm_id
JOIN quantum_backends b ON b.backend_id = e.backend_id
JOIN experiment_eligibility ee
    ON ee.experiment_id = e.experiment_id
GROUP BY a.family, b.backend
ORDER BY a.family, b.backend;

-- ============================================================
-- 28. LIFECYCLE WORKFLOW EXAMPLE
-- ============================================================

-- This transaction validates the experiment before allowing
-- its transition to VALIDATED.

DO $$
DECLARE
    result_record RECORD;
BEGIN
    SELECT *
    INTO result_record
    FROM validate_experiment(1);

    IF NOT result_record.valid THEN
        RAISE EXCEPTION
            'Experiment validation failed: %',
            result_record.validation_message;
    END IF;

    UPDATE experiments
    SET status = 'VALIDATED'
    WHERE experiment_id = 1
      AND status = 'CREATED';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment is not in CREATED state';
    END IF;
END;
$$;

-- Approval permits the next lifecycle transition.
UPDATE experiments
SET status = 'APPROVED'
WHERE experiment_id = 1
  AND status = 'VALIDATED';

-- Queue the approved experiment.
UPDATE experiments
SET status = 'QUEUED'
WHERE experiment_id = 1
  AND status = 'APPROVED';

-- Start the execution.
UPDATE experiments
SET status = 'RUNNING'
WHERE experiment_id = 1
  AND status = 'QUEUED';

INSERT INTO experiment_runs (
    experiment_id,
    run_number,
    execution_status,
    started_at,
    random_seed,
    worker_identifier
)
VALUES (
    1,
    1,
    'RUNNING',
    NOW(),
    42,
    'QML-WORKER-001'
);

-- ============================================================
-- 29. COMPLETE EXPERIMENT EXECUTION
-- ============================================================

UPDATE experiment_runs
SET
    execution_status = 'COMPLETED',
    completed_at = NOW()
WHERE experiment_id = 1
  AND run_number = 1
  AND execution_status = 'RUNNING';

INSERT INTO evaluation_metrics (
    run_id,
    accuracy,
    precision_score,
    recall_score,
    f1_score,
    training_loss,
    validation_loss,
    measurement_standard_error,
    execution_duration_ms,
    shots_used
)
SELECT
    run_id,
    0.875,
    0.857,
    0.900,
    0.878,
    0.231,
    0.264,
    0.015625,
    12000,
    2048
FROM experiment_runs
WHERE experiment_id = 1
  AND run_number = 1;

UPDATE experiments
SET status = 'COMPLETED'
WHERE experiment_id = 1
  AND status = 'RUNNING';

-- ============================================================
-- 30. FAILED EXECUTION SCENARIO
-- ============================================================

INSERT INTO experiment_runs (
    experiment_id,
    run_number,
    execution_status,
    started_at,
    error_message,
    worker_identifier
)
VALUES (
    2,
    1,
    'FAILED',
    NOW(),
    'Simulated measurement timeout.',
    'QML-WORKER-002'
);

-- ============================================================
-- 31. EVALUATION REPORT
-- ============================================================

SELECT
    e.experiment_code,
    e.experiment_name,
    a.algorithm_name,
    r.run_number,
    r.execution_status,
    m.accuracy,
    m.precision_score,
    m.recall_score,
    m.f1_score,
    m.training_loss,
    m.validation_loss,
    m.measurement_standard_error,
    m.execution_duration_ms
FROM experiments e
JOIN algorithms a ON a.algorithm_id = e.algorithm_id
JOIN experiment_runs r ON r.experiment_id = e.experiment_id
LEFT JOIN evaluation_metrics m ON m.run_id = r.run_id
ORDER BY e.experiment_code, r.run_number;

-- ============================================================
-- 32. PERFORMANCE COMPARISON
-- ============================================================

SELECT
    a.family,
    b.backend,
    COUNT(m.metric_id) AS measured_runs,
    ROUND(AVG(m.accuracy), 4) AS mean_accuracy,
    ROUND(AVG(m.training_loss), 4) AS mean_training_loss,
    ROUND(AVG(m.execution_duration_ms), 2)
        AS mean_duration_ms
FROM evaluation_metrics m
JOIN experiment_runs r ON r.run_id = m.run_id
JOIN experiments e ON e.experiment_id = r.experiment_id
JOIN algorithms a ON a.algorithm_id = e.algorithm_id
JOIN quantum_backends b ON b.backend_id = e.backend_id
GROUP BY a.family, b.backend
ORDER BY mean_accuracy DESC NULLS LAST;

-- ============================================================
-- 33. FAILURE AND AUDIT REPORT
-- ============================================================

SELECT
    e.experiment_code,
    r.run_number,
    r.error_message,
    r.execution_status,
    r.created_at
FROM experiment_runs r
JOIN experiments e ON e.experiment_id = r.experiment_id
WHERE r.execution_status IN ('FAILED', 'REJECTED')
ORDER BY r.created_at DESC;

SELECT
    e.experiment_code,
    a.action,
    a.previous_status,
    a.new_status,
    a.detail,
    a.occurred_at
FROM experiment_audit a
JOIN experiments e ON e.experiment_id = a.experiment_id
ORDER BY a.occurred_at DESC;

-- ============================================================
-- 34. CTE: APPROVED AND TECHNICALLY ELIGIBLE EXPERIMENTS
-- ============================================================

WITH approval_counts AS (
    SELECT
        experiment_id,
        COUNT(*) FILTER (
            WHERE decision = 'APPROVED'
        ) AS approvals,
        COUNT(*) FILTER (
            WHERE decision = 'REJECTED'
        ) AS rejections
    FROM experiment_approvals
    GROUP BY experiment_id
),
eligibility AS (
    SELECT
        experiment_id,
        technically_eligible
    FROM experiment_eligibility
)
SELECT
    e.experiment_code,
    e.experiment_name,
    COALESCE(ac.approvals, 0) AS approvals,
    COALESCE(ac.rejections, 0) AS rejections,
    el.technically_eligible,
    CASE
        WHEN COALESCE(ac.rejections, 0) > 0
            THEN 'GOVERNANCE_REJECTED'
        WHEN COALESCE(ac.approvals, 0) < 1
            THEN 'APPROVAL_REQUIRED'
        WHEN NOT el.technically_eligible
            THEN 'TECHNICAL_REJECTION'
        ELSE 'ELIGIBLE_FOR_EXECUTION'
    END AS execution_decision
FROM experiments e
JOIN eligibility el ON el.experiment_id = e.experiment_id
LEFT JOIN approval_counts ac
    ON ac.experiment_id = e.experiment_id
ORDER BY e.experiment_id;

-- ============================================================
-- 35. QUERY PERFORMANCE INSPECTION
-- ============================================================

EXPLAIN
SELECT
    experiment_id,
    experiment_name,
    status,
    created_at
FROM experiments
WHERE status = 'COMPLETED'
ORDER BY created_at DESC;

-- ============================================================
-- 36. TRANSACTION COMPLETION
-- ============================================================

COMMIT;
