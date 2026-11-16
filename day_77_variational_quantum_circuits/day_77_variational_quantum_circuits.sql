-- ============================================================
-- VARIATIONAL QUANTUM CIRCUITS
-- Parameterized Quantum Computation
--
-- PostgreSQL 15+
--
-- Relational experiment management and governance system.
--
-- Models:
--   Organizations
--   Researchers
--   Quantum computing backends
--   Quantum algorithms
--   Circuit architectures
--   Variational circuits
--   Circuit gates
--   Hamiltonian observables
--   Parameter sets
--   Optimization runs
--   Gradient evaluations
--   Measurement executions
--   Measurement outcomes
--   Experiment policies
--   Experiment lifecycle
--   Validation and reporting
--
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;

SET search_path TO quantum_lab, public;

-- ============================================================
-- 1. Enumerated domain types
-- ============================================================

CREATE TYPE researcher_role AS ENUM (
    'RESEARCHER',
    'PRINCIPAL_INVESTIGATOR',
    'OPERATOR',
    'AUDITOR'
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
    'RX',
    'RY',
    'RZ',
    'H',
    'CNOT',
    'CZ'
);

CREATE TYPE optimization_method AS ENUM (
    'GRADIENT_DESCENT',
    'ADAM',
    'SPSA',
    'COBYLA'
);

CREATE TYPE measurement_status AS ENUM (
    'PENDING',
    'COMPLETED',
    'FAILED'
);

CREATE TYPE backend_type AS ENUM (
    'STATE_VECTOR_SIMULATOR',
    'SHOT_BASED_SIMULATOR',
    'QUANTUM_PROCESSOR'
);

CREATE TYPE review_result AS ENUM (
    'PASS',
    'FAIL',
    'WARNING'
);

-- ============================================================
-- 2. Organizations and researchers
-- ============================================================

CREATE TABLE organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    organization_name VARCHAR(160) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES organizations(organization_id),

    username VARCHAR(80) NOT NULL UNIQUE,

    full_name VARCHAR(160) NOT NULL,

    role researcher_role NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_researchers_organization
    ON researchers(organization_id);

-- ============================================================
-- 3. Quantum backends
-- ============================================================

CREATE TABLE quantum_backends (
    backend_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    backend_name VARCHAR(120) NOT NULL UNIQUE,

    backend_kind backend_type NOT NULL,

    maximum_qubits INTEGER NOT NULL
        CHECK (maximum_qubits BETWEEN 1 AND 100000),

    supports_shots BOOLEAN NOT NULL,

    supports_state_vector BOOLEAN NOT NULL,

    gate_error_rate NUMERIC(12, 10)
        CHECK (
            gate_error_rate IS NULL
            OR gate_error_rate BETWEEN 0 AND 1
        ),

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        backend_kind <> 'STATE_VECTOR_SIMULATOR'
        OR supports_state_vector = TRUE
    )
);

-- ============================================================
-- 4. Algorithm definitions
-- ============================================================

CREATE TABLE quantum_algorithms (
    algorithm_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    algorithm_name VARCHAR(120) NOT NULL UNIQUE,

    algorithm_family VARCHAR(80) NOT NULL,

    description TEXT NOT NULL,

    is_variational BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO quantum_algorithms (
    algorithm_name,
    algorithm_family,
    description
)
VALUES
(
    'Variational Quantum Eigensolver',
    'VQE',
    'Hybrid quantum-classical optimization for estimating the ground-state energy of a Hamiltonian.'
),
(
    'Quantum Approximate Optimization Algorithm',
    'QAOA',
    'Parameterized alternating cost and mixer circuits for combinatorial optimization.'
),
(
    'Parameterized Quantum Classifier',
    'QUANTUM_ML',
    'Parameterized quantum circuit used as a trainable classification model.'
);

-- ============================================================
-- 5. Circuit architectures
-- ============================================================

CREATE TABLE circuit_architectures (
    architecture_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    architecture_name VARCHAR(120) NOT NULL UNIQUE,

    architecture_family VARCHAR(80) NOT NULL,

    entanglement_pattern VARCHAR(60) NOT NULL,

    rotation_pattern VARCHAR(60) NOT NULL,

    description TEXT NOT NULL,

    CHECK (
        entanglement_pattern IN (
            'LINEAR',
            'RING',
            'FULL',
            'NONE'
        )
    )
);

INSERT INTO circuit_architectures (
    architecture_name,
    architecture_family,
    entanglement_pattern,
    rotation_pattern,
    description
)
VALUES
(
    'Hardware Efficient Linear',
    'HARDWARE_EFFICIENT',
    'LINEAR',
    'RY_RZ',
    'Parameterized rotations connected through a linear CNOT topology.'
),
(
    'Hardware Efficient Ring',
    'HARDWARE_EFFICIENT',
    'RING',
    'RY_RZ',
    'Parameterized rotation layers with ring entanglement.'
),
(
    'Unentangled Rotation Circuit',
    'PRODUCT_STATE',
    'NONE',
    'RX_RY_RZ',
    'Independent parameterized single-qubit rotations.'
);

-- ============================================================
-- 6. Variational circuit records
-- ============================================================

CREATE TABLE variational_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    algorithm_id BIGINT NOT NULL
        REFERENCES quantum_algorithms(algorithm_id),

    architecture_id BIGINT NOT NULL
        REFERENCES circuit_architectures(architecture_id),

    owner_id BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    circuit_name VARCHAR(160) NOT NULL,

    num_qubits INTEGER NOT NULL
        CHECK (num_qubits BETWEEN 1 AND 10000),

    num_layers INTEGER NOT NULL
        CHECK (num_layers BETWEEN 1 AND 1000),

    parameter_count INTEGER NOT NULL
        CHECK (parameter_count > 0),

    circuit_version INTEGER NOT NULL DEFAULT 1
        CHECK (circuit_version > 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (owner_id, circuit_name, circuit_version)
);

CREATE INDEX idx_circuits_algorithm
    ON variational_circuits(algorithm_id);

CREATE INDEX idx_circuits_owner
    ON variational_circuits(owner_id, created_at DESC);

-- ============================================================
-- 7. Circuit gates
-- ============================================================

CREATE TABLE circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES variational_circuits(circuit_id)
        ON DELETE CASCADE,

    gate_sequence INTEGER NOT NULL
        CHECK (gate_sequence >= 0),

    gate gate_type NOT NULL,

    target_qubit INTEGER NOT NULL
        CHECK (target_qubit >= 0),

    control_qubit INTEGER,

    parameter_index INTEGER,

    UNIQUE (circuit_id, gate_sequence),

    CHECK (
        (
            gate = 'CNOT'
            AND control_qubit IS NOT NULL
            AND control_qubit <> target_qubit
            AND parameter_index IS NULL
        )
        OR
        (
            gate <> 'CNOT'
            AND control_qubit IS NULL
        )
    ),

    CHECK (
        (
            gate IN ('RX', 'RY', 'RZ')
            AND parameter_index IS NOT NULL
            AND parameter_index >= 0
        )
        OR
        (
            gate IN ('H', 'CZ')
            AND parameter_index IS NULL
        )
    )
);

CREATE INDEX idx_gates_circuit_sequence
    ON circuit_gates(circuit_id, gate_sequence);

-- Validate gate qubit indices against circuit configuration.

CREATE OR REPLACE FUNCTION validate_circuit_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    configured_qubits INTEGER;
    configured_parameters INTEGER;
BEGIN
    SELECT num_qubits, parameter_count
    INTO configured_qubits, configured_parameters
    FROM variational_circuits
    WHERE circuit_id = NEW.circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit does not exist.';
    END IF;

    IF NEW.target_qubit >= configured_qubits THEN
        RAISE EXCEPTION 'Target qubit exceeds circuit size.';
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND NEW.control_qubit >= configured_qubits THEN
        RAISE EXCEPTION 'Control qubit exceeds circuit size.';
    END IF;

    IF NEW.parameter_index IS NOT NULL
       AND NEW.parameter_index >= configured_parameters THEN
        RAISE EXCEPTION 'Parameter index exceeds circuit size.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_circuit_gate
BEFORE INSERT OR UPDATE ON circuit_gates
FOR EACH ROW
EXECUTE FUNCTION validate_circuit_gate();

-- ============================================================
-- 8. Hamiltonian definitions
-- ============================================================

CREATE TABLE hamiltonians (
    hamiltonian_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    hamiltonian_name VARCHAR(160) NOT NULL UNIQUE,

    num_qubits INTEGER NOT NULL
        CHECK (num_qubits > 0),

    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hamiltonian_terms (
    term_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    hamiltonian_id BIGINT NOT NULL
        REFERENCES hamiltonians(hamiltonian_id)
        ON DELETE CASCADE,

    pauli_string VARCHAR(10000) NOT NULL,

    coefficient NUMERIC(20, 12) NOT NULL,

    CHECK (length(pauli_string) > 0),

    CHECK (pauli_string !~ '[^IXYZ]')
);

CREATE INDEX idx_hamiltonian_terms
    ON hamiltonian_terms(hamiltonian_id);

INSERT INTO hamiltonians (
    hamiltonian_name,
    num_qubits,
    description
)
VALUES (
    'Two Qubit VQE Demonstration',
    2,
    'H = -Z0 - Z1 + 0.5 Z0Z1.'
);

INSERT INTO hamiltonian_terms (
    hamiltonian_id,
    pauli_string,
    coefficient
)
SELECT
    hamiltonian_id,
    term.pauli_string,
    term.coefficient
FROM hamiltonians
CROSS JOIN (
    VALUES
        ('ZI', -1.0::NUMERIC),
        ('IZ', -1.0::NUMERIC),
        ('ZZ', 0.5::NUMERIC)
) AS term(pauli_string, coefficient)
WHERE hamiltonian_name = 'Two Qubit VQE Demonstration';

-- ============================================================
-- 9. Experiment policies
-- ============================================================

CREATE TABLE experiment_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    maximum_qubits INTEGER NOT NULL
        CHECK (maximum_qubits > 0),

    maximum_layers INTEGER NOT NULL
        CHECK (maximum_layers > 0),

    maximum_shots INTEGER NOT NULL
        CHECK (maximum_shots > 0),

    maximum_iterations INTEGER NOT NULL
        CHECK (maximum_iterations > 0),

    allowed_optimizer optimization_method[] NOT NULL,

    require_finite_parameters BOOLEAN NOT NULL DEFAULT TRUE,

    allow_noisy_backend BOOLEAN NOT NULL DEFAULT TRUE,

    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO experiment_policies (
    policy_name,
    maximum_qubits,
    maximum_layers,
    maximum_shots,
    maximum_iterations,
    allowed_optimizer
)
VALUES (
    'Research Standard Policy',
    12,
    20,
    1000000,
    10000,
    ARRAY[
        'GRADIENT_DESCENT'::optimization_method,
        'ADAM'::optimization_method,
        'SPSA'::optimization_method
    ]
);

-- ============================================================
-- 10. Parameter sets
-- ============================================================

CREATE TABLE circuit_parameter_sets (
    parameter_set_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES variational_circuits(circuit_id),

    parameter_version INTEGER NOT NULL
        CHECK (parameter_version > 0),

    parameter_values DOUBLE PRECISION[] NOT NULL,

    created_by BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (circuit_id, parameter_version),

    CHECK (cardinality(parameter_values) > 0)
);

CREATE OR REPLACE FUNCTION validate_parameter_set()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_count INTEGER;
    invalid_count INTEGER;
BEGIN
    SELECT parameter_count
    INTO expected_count
    FROM variational_circuits
    WHERE circuit_id = NEW.circuit_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Circuit not found.';
    END IF;

    IF cardinality(NEW.parameter_values) <> expected_count THEN
        RAISE EXCEPTION
            'Expected % parameters, received %.',
            expected_count,
            cardinality(NEW.parameter_values);
    END IF;

    SELECT count(*)
    INTO invalid_count
    FROM unnest(NEW.parameter_values) AS value
    WHERE value IS NULL
       OR value::TEXT IN ('NaN', 'Infinity', '-Infinity');

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Parameters must be finite.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_parameter_set
BEFORE INSERT OR UPDATE ON circuit_parameter_sets
FOR EACH ROW
EXECUTE FUNCTION validate_parameter_set();

-- ============================================================
-- 11. Optimization runs
-- ============================================================

CREATE TABLE optimization_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    circuit_id BIGINT NOT NULL
        REFERENCES variational_circuits(circuit_id),

    parameter_set_id BIGINT NOT NULL
        REFERENCES circuit_parameter_sets(parameter_set_id),

    backend_id BIGINT NOT NULL
        REFERENCES quantum_backends(backend_id),

    hamiltonian_id BIGINT NOT NULL
        REFERENCES hamiltonians(hamiltonian_id),

    policy_id BIGINT NOT NULL
        REFERENCES experiment_policies(policy_id),

    researcher_id BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    optimizer optimization_method NOT NULL,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    learning_rate DOUBLE PRECISION NOT NULL
        CHECK (learning_rate > 0 AND learning_rate < 10),

    maximum_iterations INTEGER NOT NULL
        CHECK (maximum_iterations > 0),

    current_iteration INTEGER NOT NULL DEFAULT 0
        CHECK (current_iteration >= 0),

    initial_energy DOUBLE PRECISION,

    final_energy DOUBLE PRECISION,

    convergence_tolerance DOUBLE PRECISION NOT NULL
        CHECK (convergence_tolerance > 0),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        final_energy IS NULL
        OR final_energy <> 'NaN'::DOUBLE PRECISION
    ),

    CHECK (
        completed_at IS NULL
        OR started_at IS NULL
        OR completed_at >= started_at
    ),

    CHECK (
        status <> 'COMPLETED'
        OR final_energy IS NOT NULL
    )
);

CREATE INDEX idx_runs_status
    ON optimization_runs(status, created_at DESC);

CREATE INDEX idx_runs_circuit
    ON optimization_runs(circuit_id, created_at DESC);

CREATE INDEX idx_runs_researcher
    ON optimization_runs(researcher_id, created_at DESC);

CREATE INDEX idx_runs_active
    ON optimization_runs(created_at)
    WHERE status IN ('CREATED', 'VALIDATED', 'RUNNING');

-- ============================================================
-- 12. Gradient evaluations
-- ============================================================

CREATE TABLE gradient_evaluations (
    gradient_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    iteration INTEGER NOT NULL
        CHECK (iteration >= 0),

    parameter_index INTEGER NOT NULL
        CHECK (parameter_index >= 0),

    parameter_value DOUBLE PRECISION NOT NULL,

    gradient_value DOUBLE PRECISION NOT NULL,

    gradient_method VARCHAR(40) NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (run_id, iteration, parameter_index)
);

CREATE INDEX idx_gradients_run_iteration
    ON gradient_evaluations(run_id, iteration);

-- ============================================================
-- 13. Measurement executions
-- ============================================================

CREATE TABLE measurement_executions (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES optimization_runs(run_id),

    status measurement_status NOT NULL DEFAULT 'PENDING',

    shots INTEGER NOT NULL
        CHECK (shots > 0),

    random_seed BIGINT,

    measured_energy DOUBLE PRECISION,

    execution_time_ms NUMERIC(14, 3),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    CHECK (
        execution_time_ms IS NULL
        OR execution_time_ms >= 0
    )
);

CREATE INDEX idx_measurements_run
    ON measurement_executions(run_id);

-- ============================================================
-- 14. Measurement outcomes
-- ============================================================

CREATE TABLE measurement_outcomes (
    outcome_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    measurement_id BIGINT NOT NULL
        REFERENCES measurement_executions(measurement_id)
        ON DELETE CASCADE,

    bitstring VARCHAR(10000) NOT NULL,

    occurrence_count BIGINT NOT NULL
        CHECK (occurrence_count > 0),

    UNIQUE (measurement_id, bitstring),

    CHECK (bitstring !~ '[^01]')
);

CREATE INDEX idx_measurement_outcomes
    ON measurement_outcomes(measurement_id);

-- ============================================================
-- 15. Experiment validation records
-- ============================================================

CREATE TABLE experiment_validations (
    validation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES optimization_runs(run_id)
        ON DELETE CASCADE,

    validation_name VARCHAR(120) NOT NULL,

    result review_result NOT NULL,

    details TEXT NOT NULL,

    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (run_id, validation_name)
);

-- ============================================================
-- 16. Experiment eligibility function
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_experiment_eligibility(
    requested_run_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    run_record optimization_runs%ROWTYPE;
    circuit_record variational_circuits%ROWTYPE;
    backend_record quantum_backends%ROWTYPE;
    policy_record experiment_policies%ROWTYPE;
    parameter_record circuit_parameter_sets%ROWTYPE;
    algorithm_qubits INTEGER;
    failed_validations INTEGER;
BEGIN
    SELECT *
    INTO run_record
    FROM optimization_runs
    WHERE run_id = requested_run_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Run does not exist.';
        RETURN;
    END IF;

    SELECT *
    INTO circuit_record
    FROM variational_circuits
    WHERE circuit_id = run_record.circuit_id;

    SELECT *
    INTO backend_record
    FROM quantum_backends
    WHERE backend_id = run_record.backend_id;

    SELECT *
    INTO policy_record
    FROM experiment_policies
    WHERE policy_id = run_record.policy_id;

    SELECT *
    INTO parameter_record
    FROM circuit_parameter_sets
    WHERE parameter_set_id = run_record.parameter_set_id;

    SELECT num_qubits
    INTO algorithm_qubits
    FROM hamiltonians
    WHERE hamiltonian_id = run_record.hamiltonian_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Hamiltonian does not exist.';
        RETURN;
    END IF;

    IF run_record.status NOT IN ('CREATED', 'VALIDATED') THEN
        RETURN QUERY SELECT FALSE, 'Run is not eligible for execution.';
        RETURN;
    END IF;

    IF NOT backend_record.is_active THEN
        RETURN QUERY SELECT FALSE, 'Backend is inactive.';
        RETURN;
    END IF;

    IF NOT policy_record.is_active THEN
        RETURN QUERY SELECT FALSE, 'Experiment policy is inactive.';
        RETURN;
    END IF;

    IF circuit_record.num_qubits > backend_record.maximum_qubits THEN
        RETURN QUERY SELECT FALSE, 'Backend qubit limit exceeded.';
        RETURN;
    END IF;

    IF circuit_record.num_qubits > policy_record.maximum_qubits THEN
        RETURN QUERY SELECT FALSE, 'Policy qubit limit exceeded.';
        RETURN;
    END IF;

    IF circuit_record.num_layers > policy_record.maximum_layers THEN
        RETURN QUERY SELECT FALSE, 'Policy layer limit exceeded.';
        RETURN;
    END IF;

    IF circuit_record.num_qubits <> algorithm_qubits THEN
        RETURN QUERY SELECT FALSE, 'Hamiltonian and circuit qubits differ.';
        RETURN;
    END IF;

    IF NOT run_record.optimizer = ANY(policy_record.allowed_optimizer) THEN
        RETURN QUERY SELECT FALSE, 'Optimizer is not allowed.';
        RETURN;
    END IF;

    IF run_record.maximum_iterations > policy_record.maximum_iterations THEN
        RETURN QUERY SELECT FALSE, 'Iteration limit exceeded.';
        RETURN;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM researchers
        WHERE researcher_id = run_record.researcher_id
          AND is_active = TRUE
    ) THEN
        RETURN QUERY SELECT FALSE, 'Researcher is inactive.';
        RETURN;
    END IF;

    IF parameter_record.circuit_id <> run_record.circuit_id THEN
        RETURN QUERY SELECT FALSE, 'Parameter set belongs to another circuit.';
        RETURN;
    END IF;

    SELECT count(*)
    INTO failed_validations
    FROM experiment_validations
    WHERE run_id = requested_run_id
      AND result = 'FAIL';

    IF failed_validations > 0 THEN
        RETURN QUERY SELECT FALSE, 'Validation failures exist.';
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'All execution conditions passed.';
END;
$$;

-- ============================================================
-- 17. Controlled experiment state transitions
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_run_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'CREATED'
            AND NEW.status IN ('VALIDATED', 'FAILED', 'CANCELLED'))
        OR
        (OLD.status = 'VALIDATED'
            AND NEW.status IN ('RUNNING', 'FAILED', 'CANCELLED'))
        OR
        (OLD.status = 'RUNNING'
            AND NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED'))
    ) THEN
        RAISE EXCEPTION
            'Invalid transition: % -> %',
            OLD.status,
            NEW.status;
    END IF;

    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED')
       AND NEW.completed_at IS NULL THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_run_transition
BEFORE UPDATE OF status ON optimization_runs
FOR EACH ROW
EXECUTE FUNCTION enforce_run_transition();

-- ============================================================
-- 18. Workflow execution procedure
-- ============================================================

CREATE OR REPLACE PROCEDURE start_optimization_run(
    requested_run_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    decision RECORD;
BEGIN
    SELECT *
    INTO decision
    FROM evaluate_experiment_eligibility(requested_run_id);

    IF NOT decision.eligible THEN
        RAISE EXCEPTION
            'Experiment cannot start: %',
            decision.reason;
    END IF;

    UPDATE optimization_runs
    SET status = 'RUNNING',
        started_at = CURRENT_TIMESTAMP
    WHERE run_id = requested_run_id;

END;
$$;

-- ============================================================
-- 19. Backend sample records
-- ============================================================

INSERT INTO quantum_backends (
    backend_name,
    backend_kind,
    maximum_qubits,
    supports_shots,
    supports_state_vector,
    gate_error_rate
)
VALUES
(
    'Local State Vector Simulator',
    'STATE_VECTOR_SIMULATOR',
    24,
    TRUE,
    TRUE,
    0.0
),
(
    'Shot Based Simulator',
    'SHOT_BASED_SIMULATOR',
    20,
    TRUE,
    FALSE,
    0.0
),
(
    'Limited Quantum Processor',
    'QUANTUM_PROCESSOR',
    8,
    TRUE,
    FALSE,
    0.002
);

-- ============================================================
-- 20. Sample organization and researchers
-- ============================================================

INSERT INTO organizations (organization_name)
VALUES
('Quantum Computing Research Group'),
('Applied Quantum Algorithms Laboratory');

INSERT INTO researchers (
    organization_id,
    username,
    full_name,
    role
)
SELECT
    organization_id,
    'research_lead',
    'Research Lead',
    'PRINCIPAL_INVESTIGATOR'
FROM organizations
WHERE organization_name = 'Quantum Computing Research Group';

INSERT INTO researchers (
    organization_id,
    username,
    full_name,
    role
)
SELECT
    organization_id,
    'quantum_operator',
    'Quantum Operator',
    'OPERATOR'
FROM organizations
WHERE organization_name = 'Quantum Computing Research Group';

INSERT INTO researchers (
    organization_id,
    username,
    full_name,
    role
)
SELECT
    organization_id,
    'inactive_researcher',
    'Inactive Researcher',
    'RESEARCHER'
FROM organizations
WHERE organization_name = 'Applied Quantum Algorithms Laboratory';

UPDATE researchers
SET is_active = FALSE
WHERE username = 'inactive_researcher';

-- ============================================================
-- 21. Sample circuit
-- ============================================================

INSERT INTO variational_circuits (
    algorithm_id,
    architecture_id,
    owner_id,
    circuit_name,
    num_qubits,
    num_layers,
    parameter_count
)
SELECT
    a.algorithm_id,
    c.architecture_id,
    r.researcher_id,
    'Two Qubit VQE Circuit',
    2,
    2,
    8
FROM quantum_algorithms a
CROSS JOIN circuit_architectures c
CROSS JOIN researchers r
WHERE a.algorithm_name = 'Variational Quantum Eigensolver'
  AND c.architecture_name = 'Hardware Efficient Linear'
  AND r.username = 'research_lead';

-- ============================================================
-- 22. Sample gate sequence
-- ============================================================

INSERT INTO circuit_gates (
    circuit_id,
    gate_sequence,
    gate,
    target_qubit,
    control_qubit,
    parameter_index
)
SELECT
    circuit_id,
    gate_data.sequence,
    gate_data.gate,
    gate_data.target,
    gate_data.control,
    gate_data.parameter_index
FROM variational_circuits
CROSS JOIN (
    VALUES
        (0, 'RY'::gate_type, 0, NULL::INTEGER, 0),
        (1, 'RZ'::gate_type, 0, NULL::INTEGER, 1),
        (2, 'RY'::gate_type, 1, NULL::INTEGER, 2),
        (3, 'RZ'::gate_type, 1, NULL::INTEGER, 3),
        (4, 'CNOT'::gate_type, 1, 0, NULL::INTEGER),
        (5, 'RY'::gate_type, 0, NULL::INTEGER, 4),
        (6, 'RZ'::gate_type, 0, NULL::INTEGER, 5),
        (7, 'RY'::gate_type, 1, NULL::INTEGER, 6),
        (8, 'RZ'::gate_type, 1, NULL::INTEGER, 7),
        (9, 'CNOT'::gate_type, 1, 0, NULL::INTEGER)
) AS gate_data(
    sequence,
    gate,
    target,
    control,
    parameter_index
)
WHERE circuit_name = 'Two Qubit VQE Circuit';

-- ============================================================
-- 23. Sample parameter set
-- ============================================================

INSERT INTO circuit_parameter_sets (
    circuit_id,
    parameter_version,
    parameter_values,
    created_by
)
SELECT
    c.circuit_id,
    1,
    ARRAY[
        0.2,
        0.1,
        0.3,
        -0.2,
        0.4,
        0.1,
        -0.3,
        0.2
    ]::DOUBLE PRECISION[],
    r.researcher_id
FROM variational_circuits c
CROSS JOIN researchers r
WHERE c.circuit_name = 'Two Qubit VQE Circuit'
  AND r.username = 'research_lead';

-- ============================================================
-- 24. Sample valid optimization run
-- ============================================================

INSERT INTO optimization_runs (
    circuit_id,
    parameter_set_id,
    backend_id,
    hamiltonian_id,
    policy_id,
    researcher_id,
    optimizer,
    learning_rate,
    maximum_iterations,
    convergence_tolerance
)
SELECT
    c.circuit_id,
    p.parameter_set_id,
    b.backend_id,
    h.hamiltonian_id,
    ep.policy_id,
    r.researcher_id,
    'ADAM',
    0.04,
    150,
    0.0000001
FROM variational_circuits c
JOIN circuit_parameter_sets p
    ON p.circuit_id = c.circuit_id
JOIN quantum_backends b
    ON b.backend_name = 'Local State Vector Simulator'
JOIN hamiltonians h
    ON h.hamiltonian_name = 'Two Qubit VQE Demonstration'
JOIN experiment_policies ep
    ON ep.policy_name = 'Research Standard Policy'
JOIN researchers r
    ON r.username = 'research_lead'
WHERE c.circuit_name = 'Two Qubit VQE Circuit';

-- ============================================================
-- 25. Sample validation records
-- ============================================================

INSERT INTO experiment_validations (
    run_id,
    validation_name,
    result,
    details
)
SELECT
    run_id,
    'CIRCUIT_PARAMETER_COUNT',
    'PASS',
    'Parameter vector length matches circuit definition.'
FROM optimization_runs;

INSERT INTO experiment_validations (
    run_id,
    validation_name,
    result,
    details
)
SELECT
    run_id,
    'BACKEND_CAPACITY',
    'PASS',
    'Backend supports the configured qubit count.'
FROM optimization_runs;

-- ============================================================
-- 26. Eligibility report
-- ============================================================

SELECT
    run_id,
    eligible,
    reason
FROM optimization_runs
CROSS JOIN LATERAL
    evaluate_experiment_eligibility(run_id);

-- ============================================================
-- 27. Start valid experiment
-- ============================================================

CALL start_optimization_run(
    (SELECT min(run_id) FROM optimization_runs)
);

-- ============================================================
-- 28. Simulated optimization result
-- ============================================================

UPDATE optimization_runs
SET
    current_iteration = 25,
    initial_energy = -0.8,
    final_energy = -1.45,
    status = 'COMPLETED'
WHERE run_id = (
    SELECT min(run_id)
    FROM optimization_runs
);

-- ============================================================
-- 29. Gradient evaluation records
-- ============================================================

INSERT INTO gradient_evaluations (
    run_id,
    iteration,
    parameter_index,
    parameter_value,
    gradient_value,
    gradient_method
)
SELECT
    run_id,
    1,
    values_data.parameter_index,
    values_data.parameter_value,
    values_data.gradient_value,
    'PARAMETER_SHIFT'
FROM optimization_runs
CROSS JOIN (
    VALUES
        (0, 0.2, -0.12),
        (1, 0.1, 0.07),
        (2, 0.3, -0.18),
        (3, -0.2, 0.11),
        (4, 0.4, -0.22),
        (5, 0.1, 0.09),
        (6, -0.3, -0.14),
        (7, 0.2, 0.05)
) AS values_data(
    parameter_index,
    parameter_value,
    gradient_value
)
WHERE run_id = (
    SELECT min(run_id)
    FROM optimization_runs
);

-- ============================================================
-- 30. Measurement execution
-- ============================================================

INSERT INTO measurement_executions (
    run_id,
    status,
    shots,
    random_seed,
    measured_energy,
    execution_time_ms,
    started_at,
    completed_at
)
SELECT
    run_id,
    'COMPLETED',
    1000,
    42,
    -1.45,
    18.5,
    CURRENT_TIMESTAMP - INTERVAL '1 second',
    CURRENT_TIMESTAMP
FROM optimization_runs
WHERE run_id = (
    SELECT min(run_id)
    FROM optimization_runs
);

-- ============================================================
-- 31. Measurement outcomes
-- ============================================================

INSERT INTO measurement_outcomes (
    measurement_id,
    bitstring,
    occurrence_count
)
SELECT
    measurement_id,
    outcome.bitstring,
    outcome.occurrence_count
FROM measurement_executions
CROSS JOIN (
    VALUES
        ('00', 730::BIGINT),
        ('01', 90::BIGINT),
        ('10', 110::BIGINT),
        ('11', 70::BIGINT)
) AS outcome(bitstring, occurrence_count)
WHERE status = 'COMPLETED';

-- ============================================================
-- 32. Failed experiment example
-- ============================================================

INSERT INTO optimization_runs (
    circuit_id,
    parameter_set_id,
    backend_id,
    hamiltonian_id,
    policy_id,
    researcher_id,
    optimizer,
    learning_rate,
    maximum_iterations,
    convergence_tolerance
)
SELECT
    c.circuit_id,
    p.parameter_set_id,
    b.backend_id,
    h.hamiltonian_id,
    ep.policy_id,
    r.researcher_id,
    'ADAM',
    0.04,
    150,
    0.0000001
FROM variational_circuits c
JOIN circuit_parameter_sets p
    ON p.circuit_id = c.circuit_id
JOIN quantum_backends b
    ON b.backend_name = 'Limited Quantum Processor'
JOIN hamiltonians h
    ON h.hamiltonian_name = 'Two Qubit VQE Demonstration'
JOIN experiment_policies ep
    ON ep.policy_name = 'Research Standard Policy'
JOIN researchers r
    ON r.username = 'research_lead'
WHERE c.circuit_name = 'Two Qubit VQE Circuit';

INSERT INTO experiment_validations (
    run_id,
    validation_name,
    result,
    details
)
SELECT
    run_id,
    'SIMULATED_BACKEND_CHECK',
    'FAIL',
    'Demonstration failure record for an unavailable backend configuration.'
FROM optimization_runs
WHERE backend_id = (
    SELECT backend_id
    FROM quantum_backends
    WHERE backend_name = 'Limited Quantum Processor'
);

-- ============================================================
-- 33. Measurement aggregation view
-- ============================================================

CREATE OR REPLACE VIEW measurement_summary AS
SELECT
    m.measurement_id,
    m.run_id,
    m.status,
    m.shots,
    COALESCE(
        SUM(o.occurrence_count),
        0
    ) AS recorded_shots,
    COUNT(o.outcome_id) AS distinct_outcomes,
    CASE
        WHEN m.shots = 0 THEN 0
        ELSE COALESCE(
            SUM(o.occurrence_count),
            0
        )::NUMERIC / m.shots
    END AS recording_completeness
FROM measurement_executions m
LEFT JOIN measurement_outcomes o
    ON o.measurement_id = m.measurement_id
GROUP BY
    m.measurement_id,
    m.run_id,
    m.status,
    m.shots;

-- ============================================================
-- 34. Research experiment reporting view
-- ============================================================

CREATE OR REPLACE VIEW experiment_report AS
SELECT
    r.run_id,
    c.circuit_name,
    c.num_qubits,
    c.num_layers,
    a.algorithm_name,
    b.backend_name,
    r.optimizer,
    r.status,
    r.initial_energy,
    r.final_energy,
    r.current_iteration,
    researcher.username AS owner,
    r.created_at,
    r.completed_at,
    CASE
        WHEN r.initial_energy IS NULL
          OR r.final_energy IS NULL
        THEN NULL
        ELSE r.initial_energy - r.final_energy
    END AS energy_improvement
FROM optimization_runs r
JOIN variational_circuits c
    ON c.circuit_id = r.circuit_id
JOIN quantum_algorithms a
    ON a.algorithm_id = c.algorithm_id
JOIN quantum_backends b
    ON b.backend_id = r.backend_id
JOIN researchers researcher
    ON researcher.researcher_id = r.researcher_id;

-- ============================================================
-- 35. Retrieval
-- ============================================================

SELECT *
FROM experiment_report
ORDER BY created_at DESC;

-- ============================================================
-- 36. Aggregation
-- ============================================================

SELECT
    optimizer,
    status,
    COUNT(*) AS total_runs,
    AVG(final_energy) AS mean_final_energy,
    MIN(final_energy) AS best_final_energy,
    AVG(current_iteration) AS mean_iterations
FROM optimization_runs
GROUP BY optimizer, status
ORDER BY optimizer, status;

-- ============================================================
-- 37. Gradient diagnostics
-- ============================================================

SELECT
    run_id,
    iteration,
    COUNT(*) AS evaluated_parameters,
    AVG(ABS(gradient_value)) AS mean_absolute_gradient,
    MAX(ABS(gradient_value)) AS maximum_absolute_gradient,
    SQRT(SUM(gradient_value * gradient_value)) AS gradient_norm
FROM gradient_evaluations
GROUP BY run_id, iteration
ORDER BY run_id, iteration;

-- ============================================================
-- 38. Measurement quality assessment
-- ============================================================

SELECT
    measurement_id,
    shots,
    recorded_shots,
    distinct_outcomes,
    recording_completeness,
    CASE
        WHEN recorded_shots = shots THEN 'COMPLETE'
        WHEN recorded_shots < shots THEN 'INCOMPLETE'
        ELSE 'INVALID'
    END AS quality_status
FROM measurement_summary;

-- ============================================================
-- 39. Failed validation report
-- ============================================================

SELECT
    r.run_id,
    c.circuit_name,
    v.validation_name,
    v.details
FROM experiment_validations v
JOIN optimization_runs r
    ON r.run_id = v.run_id
JOIN variational_circuits c
    ON c.circuit_id = r.circuit_id
WHERE v.result = 'FAIL';

-- ============================================================
-- 40. Transactional parameter-version creation
-- ============================================================

-- The version is derived under a transaction.
-- FOR UPDATE serializes competing version assignments.

DO $$
DECLARE
    selected_circuit BIGINT;
    selected_researcher BIGINT;
    next_version INTEGER;
    parameter_count_value INTEGER;
    new_values DOUBLE PRECISION[];
BEGIN
    SELECT circuit_id, parameter_count
    INTO selected_circuit, parameter_count_value
    FROM variational_circuits
    WHERE circuit_name = 'Two Qubit VQE Circuit'
    FOR UPDATE;

    SELECT researcher_id
    INTO selected_researcher
    FROM researchers
    WHERE username = 'research_lead';

    SELECT COALESCE(MAX(parameter_version), 0) + 1
    INTO next_version
    FROM circuit_parameter_sets
    WHERE circuit_id = selected_circuit;

    SELECT array_agg(0.01::DOUBLE PRECISION)
    INTO new_values
    FROM generate_series(1, parameter_count_value);

    INSERT INTO circuit_parameter_sets (
        circuit_id,
        parameter_version,
        parameter_values,
        created_by
    )
    VALUES (
        selected_circuit,
        next_version,
        new_values,
        selected_researcher
    );
END;
$$;

-- ============================================================
-- 41. Security and operational notes
-- ============================================================

-- In production:
-- 1. Use separate database roles for researchers and operators.
-- 2. Restrict direct modifications to optimization_runs.
-- 3. Expose state transitions through controlled procedures.
-- 4. Apply row-level security for organization isolation.
-- 5. Do not store API keys, credentials or private hardware tokens.
-- 6. Record hardware job identifiers separately from local run IDs.
-- 7. Keep experiment artifacts in controlled object storage.
-- 8. Avoid unrestricted SQL execution by application users.

-- Example organization isolation policy.

ALTER TABLE variational_circuits
    ENABLE ROW LEVEL SECURITY;

-- The following policy assumes the application sets
-- quantum_lab.organization_id to the authenticated organization.
--
-- SET LOCAL quantum_lab.organization_id = '1';
--
-- CREATE POLICY circuit_organization_isolation
-- ON variational_circuits
-- USING (
--     EXISTS (
--         SELECT 1
--         FROM researchers r
--         WHERE r.researcher_id = variational_circuits.owner_id
--           AND r.organization_id =
--               current_setting(
--                   'quantum_lab.organization_id',
--                   true
--               )::BIGINT
--     )
-- );

COMMIT;

-- ============================================================
-- END OF VARIATIONAL QUANTUM CIRCUIT DATABASE
-- ============================================================
