/*
 * PostgreSQL VQE Experiment Management System
 *
 * Application:
 * Molecular hydrogen ground-state energy optimization.
 *
 * Database capabilities:
 * - Molecular Hamiltonian storage
 * - Pauli operator definitions
 * - Ansatz configurations
 * - Optimization policies
 * - Experiment lifecycle
 * - Iteration history
 * - Parameter vectors
 * - Measurement results
 * - Exact-reference validation
 * - Energy convergence reporting
 * - Transaction-safe experiment updates
 *
 * Compatible with PostgreSQL 15+.
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_vqe;

SET search_path TO quantum_vqe, public;

-- -------------------------------------------------------
-- 1. Enumerated domain types
-- -------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE optimizer_type AS ENUM (
    'ADAM',
    'SGD',
    'COBYLA',
    'SPSA'
);

CREATE TYPE measurement_basis AS ENUM (
    'COMPUTATIONAL',
    'X',
    'Y',
    'Z'
);

CREATE TYPE validation_status AS ENUM (
    'PENDING',
    'PASSED',
    'FAILED'
);

-- -------------------------------------------------------
-- 2. Molecular systems
-- -------------------------------------------------------

CREATE TABLE molecules (
    molecule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    molecular_formula VARCHAR(30) NOT NULL,
    molecular_name VARCHAR(100) NOT NULL,
    basis_set VARCHAR(50) NOT NULL,
    geometry_description TEXT NOT NULL,
    internuclear_distance_angstrom NUMERIC(12,8),
    electron_count INTEGER NOT NULL,
    nuclear_charge INTEGER NOT NULL,
    energy_unit VARCHAR(20) NOT NULL DEFAULT 'Hartree',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_molecular_configuration
        UNIQUE (
            molecular_formula,
            basis_set,
            geometry_description
        ),

    CONSTRAINT valid_electron_count
        CHECK (electron_count > 0),

    CONSTRAINT valid_nuclear_charge
        CHECK (nuclear_charge > 0),

    CONSTRAINT valid_internuclear_distance
        CHECK (
            internuclear_distance_angstrom IS NULL
            OR internuclear_distance_angstrom > 0
        ),

    CONSTRAINT valid_energy_unit
        CHECK (energy_unit IN ('Hartree', 'eV'))
);

-- -------------------------------------------------------
-- 3. Molecular Hamiltonians
-- -------------------------------------------------------

CREATE TABLE hamiltonians (
    hamiltonian_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    molecule_id BIGINT NOT NULL
        REFERENCES molecules(molecule_id),

    hamiltonian_name VARCHAR(120) NOT NULL,
    qubit_count INTEGER NOT NULL,
    representation VARCHAR(50) NOT NULL DEFAULT 'Pauli decomposition',
    reference_ground_energy NUMERIC(20,14),
    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_hamiltonian
        UNIQUE (molecule_id, hamiltonian_name),

    CONSTRAINT valid_qubit_count
        CHECK (qubit_count BETWEEN 1 AND 30),

    CONSTRAINT finite_reference_energy
        CHECK (
            reference_ground_energy IS NULL
            OR reference_ground_energy BETWEEN -100000 AND 100000
        )
);

CREATE TABLE hamiltonian_terms (
    term_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hamiltonian_id BIGINT NOT NULL
        REFERENCES hamiltonians(hamiltonian_id)
        ON DELETE CASCADE,

    pauli_string VARCHAR(30) NOT NULL,
    coefficient NUMERIC(24,16) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_pauli_term
        UNIQUE (hamiltonian_id, pauli_string),

    CONSTRAINT valid_pauli_string
        CHECK (pauli_string ~ '^[IXYZ]+$'),

    CONSTRAINT valid_coefficient
        CHECK (coefficient BETWEEN -100000 AND 100000)
);

CREATE INDEX idx_hamiltonian_terms
    ON hamiltonian_terms(hamiltonian_id);

-- -------------------------------------------------------
-- 4. Ansatz definitions
-- -------------------------------------------------------

CREATE TABLE ansatz_definitions (
    ansatz_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    ansatz_name VARCHAR(120) NOT NULL UNIQUE,
    ansatz_type VARCHAR(50) NOT NULL,
    qubit_count INTEGER NOT NULL,
    parameter_count INTEGER NOT NULL,
    circuit_description TEXT NOT NULL,
    entanglement_pattern VARCHAR(100) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_ansatz_qubits
        CHECK (qubit_count > 0),

    CONSTRAINT valid_parameter_count
        CHECK (parameter_count >= 0)
);

-- -------------------------------------------------------
-- 5. Optimization policies
-- -------------------------------------------------------

CREATE TABLE optimization_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(100) NOT NULL UNIQUE,
    optimizer optimizer_type NOT NULL,

    learning_rate NUMERIC(16,12) NOT NULL,
    beta1 NUMERIC(12,10) NOT NULL DEFAULT 0.9,
    beta2 NUMERIC(12,10) NOT NULL DEFAULT 0.999,
    epsilon NUMERIC(16,14) NOT NULL DEFAULT 0.00000001,

    convergence_tolerance NUMERIC(16,12) NOT NULL,
    maximum_iterations INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_learning_rate
        CHECK (learning_rate > 0),

    CONSTRAINT valid_beta1
        CHECK (beta1 > 0 AND beta1 < 1),

    CONSTRAINT valid_beta2
        CHECK (beta2 > 0 AND beta2 < 1),

    CONSTRAINT valid_epsilon
        CHECK (epsilon > 0),

    CONSTRAINT valid_tolerance
        CHECK (convergence_tolerance > 0),

    CONSTRAINT valid_maximum_iterations
        CHECK (maximum_iterations > 0)
);

-- -------------------------------------------------------
-- 6. Experiment records
-- -------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(80) NOT NULL UNIQUE,

    molecule_id BIGINT NOT NULL
        REFERENCES molecules(molecule_id),

    hamiltonian_id BIGINT NOT NULL
        REFERENCES hamiltonians(hamiltonian_id),

    ansatz_id BIGINT NOT NULL
        REFERENCES ansatz_definitions(ansatz_id),

    policy_id BIGINT NOT NULL
        REFERENCES optimization_policies(policy_id),

    status experiment_status NOT NULL DEFAULT 'CREATED',

    optimized_energy NUMERIC(24,16),
    exact_energy NUMERIC(24,16),
    absolute_error NUMERIC(24,16),

    final_iteration INTEGER,

    converged BOOLEAN NOT NULL DEFAULT FALSE,

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_optimized_energy
        CHECK (
            optimized_energy IS NULL
            OR optimized_energy BETWEEN -100000 AND 100000
        ),

    CONSTRAINT valid_exact_energy
        CHECK (
            exact_energy IS NULL
            OR exact_energy BETWEEN -100000 AND 100000
        ),

    CONSTRAINT valid_absolute_error
        CHECK (absolute_error IS NULL OR absolute_error >= 0),

    CONSTRAINT valid_final_iteration
        CHECK (final_iteration IS NULL OR final_iteration >= 0),

    CONSTRAINT valid_experiment_timestamps
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT completed_experiment_has_energy
        CHECK (
            status <> 'COMPLETED'
            OR (
                optimized_energy IS NOT NULL
                AND exact_energy IS NOT NULL
                AND absolute_error IS NOT NULL
                AND completed_at IS NOT NULL
            )
        )
);

CREATE INDEX idx_experiments_status
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_molecule
    ON experiments(molecule_id, created_at DESC);

CREATE INDEX idx_experiments_energy
    ON experiments(optimized_energy)
    WHERE status = 'COMPLETED';

-- -------------------------------------------------------
-- 7. Parameter vectors
-- -------------------------------------------------------

CREATE TABLE experiment_parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    parameter_index INTEGER NOT NULL,
    parameter_value NUMERIC(24,16) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_experiment_parameter
        UNIQUE (experiment_id, parameter_index),

    CONSTRAINT valid_parameter_index
        CHECK (parameter_index >= 0),

    CONSTRAINT valid_parameter_value
        CHECK (parameter_value BETWEEN -100000 AND 100000)
);

-- -------------------------------------------------------
-- 8. Optimization history
-- -------------------------------------------------------

CREATE TABLE optimization_iterations (
    iteration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    iteration_number INTEGER NOT NULL,

    energy NUMERIC(24,16) NOT NULL,
    gradient_norm NUMERIC(24,16) NOT NULL,

    learning_rate NUMERIC(16,12) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_experiment_iteration
        UNIQUE (experiment_id, iteration_number),

    CONSTRAINT valid_iteration_number
        CHECK (iteration_number > 0),

    CONSTRAINT valid_gradient_norm
        CHECK (gradient_norm >= 0),

    CONSTRAINT valid_iteration_learning_rate
        CHECK (learning_rate > 0)
);

CREATE INDEX idx_iteration_energy
    ON optimization_iterations(experiment_id, iteration_number);

-- -------------------------------------------------------
-- 9. Measurement results
-- -------------------------------------------------------

CREATE TABLE measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    measurement_basis measurement_basis NOT NULL,

    basis_state VARCHAR(30) NOT NULL,

    shots INTEGER NOT NULL,
    observed_count INTEGER NOT NULL,

    probability NUMERIC(18,16) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_measurement_shots
        CHECK (shots > 0),

    CONSTRAINT valid_observed_count
        CHECK (observed_count >= 0 AND observed_count <= shots),

    CONSTRAINT valid_probability
        CHECK (probability >= 0 AND probability <= 1),

    CONSTRAINT unique_measurement_result
        UNIQUE (
            experiment_id,
            measurement_basis,
            basis_state
        )
);

-- -------------------------------------------------------
-- 10. Experiment validation
-- -------------------------------------------------------

CREATE TABLE experiment_validations (
    validation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    validation_name VARCHAR(120) NOT NULL,

    validation_status validation_status NOT NULL DEFAULT 'PENDING',

    observed_value NUMERIC(24,16),
    expected_value NUMERIC(24,16),

    details TEXT,

    validated_at TIMESTAMPTZ,

    CONSTRAINT unique_experiment_validation
        UNIQUE (experiment_id, validation_name)
);

-- -------------------------------------------------------
-- 11. Data-integrity triggers
-- -------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_hamiltonian_qubits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO expected_qubits
    FROM hamiltonians
    WHERE hamiltonian_id = NEW.hamiltonian_id;

    IF expected_qubits IS NULL THEN
        RAISE EXCEPTION 'Hamiltonian does not exist.';
    END IF;

    IF length(NEW.pauli_string) <> expected_qubits THEN
        RAISE EXCEPTION
            'Pauli string length % does not match qubit count %.',
            length(NEW.pauli_string),
            expected_qubits;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_hamiltonian_qubits
BEFORE INSERT OR UPDATE ON hamiltonian_terms
FOR EACH ROW
EXECUTE FUNCTION validate_hamiltonian_qubits();


CREATE OR REPLACE FUNCTION validate_experiment_relationships()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    molecule_from_hamiltonian BIGINT;
    hamiltonian_qubits INTEGER;
    ansatz_qubits INTEGER;
BEGIN
    SELECT molecule_id, qubit_count
    INTO molecule_from_hamiltonian, hamiltonian_qubits
    FROM hamiltonians
    WHERE hamiltonian_id = NEW.hamiltonian_id;

    SELECT qubit_count
    INTO ansatz_qubits
    FROM ansatz_definitions
    WHERE ansatz_id = NEW.ansatz_id;

    IF molecule_from_hamiltonian IS DISTINCT FROM NEW.molecule_id THEN
        RAISE EXCEPTION
            'Experiment molecule does not match Hamiltonian molecule.';
    END IF;

    IF hamiltonian_qubits IS DISTINCT FROM ansatz_qubits THEN
        RAISE EXCEPTION
            'Ansatz and Hamiltonian qubit counts do not match.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment_relationships
BEFORE INSERT OR UPDATE OF molecule_id, hamiltonian_id, ansatz_id
ON experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment_relationships();


CREATE OR REPLACE FUNCTION enforce_experiment_state()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IN ('COMPLETED', 'FAILED', 'CANCELLED')
       AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION
            'Terminal experiment status cannot be changed.';
    END IF;

    IF OLD.status = 'CREATED'
       AND NEW.status NOT IN ('CREATED', 'RUNNING', 'FAILED', 'CANCELLED') THEN
        RAISE EXCEPTION 'Invalid experiment state transition.';
    END IF;

    IF OLD.status = 'RUNNING'
       AND NEW.status NOT IN ('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED') THEN
        RAISE EXCEPTION 'Invalid experiment state transition.';
    END IF;

    IF OLD.status = 'CREATED' AND NEW.status = 'RUNNING' THEN
        NEW.started_at = COALESCE(NEW.started_at, CURRENT_TIMESTAMP);
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = COALESCE(
            NEW.completed_at,
            CURRENT_TIMESTAMP
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_enforce_experiment_state
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_state();


CREATE OR REPLACE FUNCTION prevent_iteration_after_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Iterations can only be recorded for RUNNING experiments.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_iteration_after_completion
BEFORE INSERT ON optimization_iterations
FOR EACH ROW
EXECUTE FUNCTION prevent_iteration_after_completion();


CREATE OR REPLACE FUNCTION prevent_parameter_after_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Parameters can only be recorded for RUNNING experiments.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_parameter_after_completion
BEFORE INSERT OR UPDATE ON experiment_parameters
FOR EACH ROW
EXECUTE FUNCTION prevent_parameter_after_completion();


-- -------------------------------------------------------
-- 12. Experiment eligibility function
-- -------------------------------------------------------

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
    current_status experiment_status;
    current_hamiltonian BIGINT;
    term_count INTEGER;
    parameter_count INTEGER;
    required_parameters INTEGER;
    qubit_count INTEGER;
BEGIN
    SELECT
        e.status,
        e.hamiltonian_id,
        h.qubit_count,
        a.parameter_count
    INTO
        current_status,
        current_hamiltonian,
        qubit_count,
        required_parameters
    FROM experiments e
    JOIN hamiltonians h
        ON h.hamiltonian_id = e.hamiltonian_id
    JOIN ansatz_definitions a
        ON a.ansatz_id = e.ansatz_id
    WHERE e.experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Experiment not found'::TEXT;
        RETURN;
    END IF;

    IF current_status <> 'RUNNING' THEN
        RETURN QUERY SELECT FALSE, 'Experiment is not RUNNING'::TEXT;
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO term_count
    FROM hamiltonian_terms
    WHERE hamiltonian_id = current_hamiltonian;

    IF term_count = 0 THEN
        RETURN QUERY SELECT FALSE, 'Hamiltonian has no terms'::TEXT;
        RETURN;
    END IF;

    SELECT COUNT(*)
    INTO parameter_count
    FROM experiment_parameters
    WHERE experiment_id = p_experiment_id;

    IF parameter_count <> required_parameters THEN
        RETURN QUERY SELECT FALSE,
            'Initial parameter vector is incomplete'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY SELECT TRUE, 'Experiment is eligible'::TEXT;
END;
$$;

-- -------------------------------------------------------
-- 13. Procedure for recording an optimization iteration
-- -------------------------------------------------------

CREATE OR REPLACE PROCEDURE record_iteration(
    p_experiment_id BIGINT,
    p_iteration INTEGER,
    p_energy NUMERIC,
    p_gradient_norm NUMERIC,
    p_learning_rate NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    previous_iteration INTEGER;
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment not found.';
    END IF;

    IF current_status <> 'RUNNING' THEN
        RAISE EXCEPTION 'Experiment must be RUNNING.';
    END IF;

    SELECT COALESCE(MAX(iteration_number), 0)
    INTO previous_iteration
    FROM optimization_iterations
    WHERE experiment_id = p_experiment_id;

    IF p_iteration <> previous_iteration + 1 THEN
        RAISE EXCEPTION
            'Expected iteration %, received %.',
            previous_iteration + 1,
            p_iteration;
    END IF;

    INSERT INTO optimization_iterations (
        experiment_id,
        iteration_number,
        energy,
        gradient_norm,
        learning_rate
    )
    VALUES (
        p_experiment_id,
        p_iteration,
        p_energy,
        p_gradient_norm,
        p_learning_rate
    );

    UPDATE experiments
    SET final_iteration = p_iteration
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- -------------------------------------------------------
-- 14. Complete experiment procedure
-- -------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_experiment(
    p_experiment_id BIGINT,
    p_optimized_energy NUMERIC,
    p_exact_energy NUMERIC,
    p_converged BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE experiments
    SET
        optimized_energy = p_optimized_energy,
        exact_energy = p_exact_energy,
        absolute_error = ABS(p_optimized_energy - p_exact_energy),
        converged = p_converged,
        status = 'COMPLETED'
    WHERE experiment_id = p_experiment_id
      AND status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Only RUNNING experiments can be completed.';
    END IF;
END;
$$;

-- -------------------------------------------------------
-- 15. Reporting views
-- -------------------------------------------------------

CREATE VIEW v_experiment_summary AS
SELECT
    e.experiment_id,
    e.experiment_code,
    m.molecular_formula,
    m.molecular_name,
    h.hamiltonian_name,
    a.ansatz_name,
    p.optimizer,
    e.status,
    e.optimized_energy,
    e.exact_energy,
    e.absolute_error,
    e.converged,
    e.final_iteration,
    e.started_at,
    e.completed_at
FROM experiments e
JOIN molecules m
    ON m.molecule_id = e.molecule_id
JOIN hamiltonians h
    ON h.hamiltonian_id = e.hamiltonian_id
JOIN ansatz_definitions a
    ON a.ansatz_id = e.ansatz_id
JOIN optimization_policies p
    ON p.policy_id = e.policy_id;


CREATE VIEW v_energy_convergence AS
SELECT
    experiment_id,
    iteration_number,
    energy,
    gradient_norm,
    energy - LAG(energy) OVER (
        PARTITION BY experiment_id
        ORDER BY iteration_number
    ) AS energy_change,
    MIN(energy) OVER (
        PARTITION BY experiment_id
        ORDER BY iteration_number
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS best_energy_so_far
FROM optimization_iterations;


CREATE VIEW v_measurement_statistics AS
SELECT
    experiment_id,
    measurement_basis,
    SUM(observed_count) AS total_observations,
    SUM(shots) AS recorded_shots,
    SUM(probability) AS total_recorded_probability
FROM measurements
GROUP BY experiment_id, measurement_basis;

-- -------------------------------------------------------
-- 16. Seed molecular and algorithmic configurations
-- -------------------------------------------------------

INSERT INTO molecules (
    molecular_formula,
    molecular_name,
    basis_set,
    geometry_description,
    internuclear_distance_angstrom,
    electron_count,
    nuclear_charge
)
VALUES (
    'H2',
    'Molecular Hydrogen',
    'STO-3G',
    'Linear hydrogen molecule, reduced two-qubit model',
    0.735,
    2,
    2
);

INSERT INTO hamiltonians (
    molecule_id,
    hamiltonian_name,
    qubit_count,
    reference_ground_energy,
    description
)
SELECT
    molecule_id,
    'H2_REDUCED_TWO_QUBIT',
    2,
    -1.8572750302023802,
    'Reduced two-qubit Pauli Hamiltonian in Hartree units'
FROM molecules
WHERE molecular_formula = 'H2';

INSERT INTO hamiltonian_terms (
    hamiltonian_id,
    pauli_string,
    coefficient
)
SELECT
    hamiltonian_id,
    term.pauli_string,
    term.coefficient
FROM hamiltonians h
CROSS JOIN (
    VALUES
        ('II', -1.052373245772859::NUMERIC),
        ('ZI', 0.39793742484318045::NUMERIC),
        ('IZ', -0.39793742484318045::NUMERIC),
        ('ZZ', -0.01128010425623538::NUMERIC),
        ('XX', 0.18093119978423156::NUMERIC)
) AS term(pauli_string, coefficient)
WHERE h.hamiltonian_name = 'H2_REDUCED_TWO_QUBIT';

INSERT INTO ansatz_definitions (
    ansatz_name,
    ansatz_type,
    qubit_count,
    parameter_count,
    circuit_description,
    entanglement_pattern
)
VALUES (
    'TWO_QUBIT_RY_CNOT',
    'Hardware-efficient',
    2,
    2,
    'RY(theta0) on qubit 0, RY(theta1) on qubit 1, CNOT(0,1)',
    'Linear CNOT'
);

INSERT INTO optimization_policies (
    policy_name,
    optimizer,
    learning_rate,
    beta1,
    beta2,
    epsilon,
    convergence_tolerance,
    maximum_iterations
)
VALUES (
    'ADAM_STANDARD',
    'ADAM',
    0.05,
    0.9,
    0.999,
    0.00000001,
    0.000000001,
    2000
);

-- -------------------------------------------------------
-- 17. Create sample experiment
-- -------------------------------------------------------

INSERT INTO experiments (
    experiment_code,
    molecule_id,
    hamiltonian_id,
    ansatz_id,
    policy_id,
    status
)
SELECT
    'H2-VQE-001',
    m.molecule_id,
    h.hamiltonian_id,
    a.ansatz_id,
    p.policy_id,
    'CREATED'
FROM molecules m
JOIN hamiltonians h
    ON h.molecule_id = m.molecule_id
JOIN ansatz_definitions a
    ON a.ansatz_name = 'TWO_QUBIT_RY_CNOT'
JOIN optimization_policies p
    ON p.policy_name = 'ADAM_STANDARD'
WHERE m.molecular_formula = 'H2';

-- -------------------------------------------------------
-- 18. Transactional experiment initialization
-- -------------------------------------------------------

DO $$
DECLARE
    experiment_key BIGINT;
BEGIN
    SELECT experiment_id
    INTO experiment_key
    FROM experiments
    WHERE experiment_code = 'H2-VQE-001';

    UPDATE experiments
    SET status = 'RUNNING'
    WHERE experiment_id = experiment_key
      AND status = 'CREATED';

    INSERT INTO experiment_parameters (
        experiment_id,
        parameter_index,
        parameter_value
    )
    VALUES
        (experiment_key, 0, 0.2),
        (experiment_key, 1, -0.4);

    RAISE NOTICE 'Experiment % initialized.', experiment_key;
END;
$$;

-- -------------------------------------------------------
-- 19. Demonstrate eligibility determination
-- -------------------------------------------------------

SELECT *
FROM check_experiment_eligibility(
    (SELECT experiment_id
     FROM experiments
     WHERE experiment_code = 'H2-VQE-001')
);

-- -------------------------------------------------------
-- 20. Record representative optimization iterations
-- -------------------------------------------------------

CALL record_iteration(
    (SELECT experiment_id FROM experiments
     WHERE experiment_code = 'H2-VQE-001'),
    1,
    -1.5000000000000000,
    0.3500000000000000,
    0.05
);

CALL record_iteration(
    (SELECT experiment_id FROM experiments
     WHERE experiment_code = 'H2-VQE-001'),
    2,
    -1.6200000000000000,
    0.2400000000000000,
    0.05
);

CALL record_iteration(
    (SELECT experiment_id FROM experiments
     WHERE experiment_code = 'H2-VQE-001'),
    3,
    -1.7300000000000000,
    0.1200000000000000,
    0.05
);

CALL record_iteration(
    (SELECT experiment_id FROM experiments
     WHERE experiment_code = 'H2-VQE-001'),
    4,
    -1.8100000000000000,
    0.0400000000000000,
    0.05
);

-- -------------------------------------------------------
-- 21. Store measurement results
-- -------------------------------------------------------

INSERT INTO measurements (
    experiment_id,
    measurement_basis,
    basis_state,
    shots,
    observed_count,
    probability
)
SELECT
    experiment_id,
    'COMPUTATIONAL',
    '00',
    10000,
    7200,
    0.72
FROM experiments
WHERE experiment_code = 'H2-VQE-001';

INSERT INTO measurements (
    experiment_id,
    measurement_basis,
    basis_state,
    shots,
    observed_count,
    probability
)
SELECT
    experiment_id,
    'COMPUTATIONAL',
    '11',
    10000,
    2800,
    0.28
FROM experiments
WHERE experiment_code = 'H2-VQE-001';

-- -------------------------------------------------------
-- 22. Store validation results
-- -------------------------------------------------------

INSERT INTO experiment_validations (
    experiment_id,
    validation_name,
    validation_status,
    observed_value,
    expected_value,
    details,
    validated_at
)
SELECT
    experiment_id,
    'HAMILTONIAN_HERMITICITY',
    'PASSED',
    1,
    1,
    'Hamiltonian matrix is Hermitian.',
    CURRENT_TIMESTAMP
FROM experiments
WHERE experiment_code = 'H2-VQE-001';

INSERT INTO experiment_validations (
    experiment_id,
    validation_name,
    validation_status,
    observed_value,
    expected_value,
    details,
    validated_at
)
SELECT
    experiment_id,
    'STATE_NORMALIZATION',
    'PASSED',
    1,
    1,
    'Statevector normalization equals one.',
    CURRENT_TIMESTAMP
FROM experiments
WHERE experiment_code = 'H2-VQE-001';

-- -------------------------------------------------------
-- 23. Complete sample experiment
-- -------------------------------------------------------

CALL complete_experiment(
    (SELECT experiment_id FROM experiments
     WHERE experiment_code = 'H2-VQE-001'),
    -1.8100000000000000,
    -1.8572750302023802,
    FALSE
);

-- -------------------------------------------------------
-- 24. Additional failure-state demonstration
-- -------------------------------------------------------

INSERT INTO experiments (
    experiment_code,
    molecule_id,
    hamiltonian_id,
    ansatz_id,
    policy_id,
    status,
    failure_reason
)
SELECT
    'H2-VQE-FAILED-001',
    m.molecule_id,
    h.hamiltonian_id,
    a.ansatz_id,
    p.policy_id,
    'FAILED',
    'Illustrative numerical instability during optimization.'
FROM molecules m
JOIN hamiltonians h
    ON h.molecule_id = m.molecule_id
JOIN ansatz_definitions a
    ON a.ansatz_name = 'TWO_QUBIT_RY_CNOT'
JOIN optimization_policies p
    ON p.policy_name = 'ADAM_STANDARD'
WHERE m.molecular_formula = 'H2';

-- -------------------------------------------------------
-- 25. Retrieval queries
-- -------------------------------------------------------

SELECT *
FROM v_experiment_summary
ORDER BY created_at DESC NULLS LAST;

SELECT
    h.hamiltonian_name,
    t.pauli_string,
    t.coefficient
FROM hamiltonian_terms t
JOIN hamiltonians h
    ON h.hamiltonian_id = t.hamiltonian_id
ORDER BY t.term_id;

-- -------------------------------------------------------
-- 26. Optimization convergence analysis
-- -------------------------------------------------------

SELECT
    experiment_id,
    iteration_number,
    energy,
    energy_change,
    best_energy_so_far,
    gradient_norm
FROM v_energy_convergence
ORDER BY experiment_id, iteration_number;

-- -------------------------------------------------------
-- 27. Experiment performance aggregation
-- -------------------------------------------------------

SELECT
    m.molecular_formula,
    COUNT(*) AS experiment_count,
    AVG(e.absolute_error) AS mean_absolute_error,
    MIN(e.optimized_energy) AS lowest_observed_energy,
    MAX(e.final_iteration) AS maximum_iterations,
    COUNT(*) FILTER (WHERE e.converged) AS converged_experiments,
    COUNT(*) FILTER (
        WHERE e.status = 'FAILED'
    ) AS failed_experiments
FROM experiments e
JOIN molecules m
    ON m.molecule_id = e.molecule_id
GROUP BY m.molecular_formula;

-- -------------------------------------------------------
-- 28. Measurement reporting
-- -------------------------------------------------------

SELECT *
FROM v_measurement_statistics
ORDER BY experiment_id;

-- -------------------------------------------------------
-- 29. Validation reporting
-- -------------------------------------------------------

SELECT
    e.experiment_code,
    v.validation_name,
    v.validation_status,
    v.details
FROM experiment_validations v
JOIN experiments e
    ON e.experiment_id = v.experiment_id
ORDER BY e.experiment_code, v.validation_name;

-- -------------------------------------------------------
-- 30. Variational principle evaluation
-- -------------------------------------------------------

SELECT
    experiment_code,
    optimized_energy,
    exact_energy,
    absolute_error,
    CASE
        WHEN optimized_energy >= exact_energy - 0.0000001
        THEN 'VARIATIONAL_BOUND_SATISFIED'
        ELSE 'VARIATIONAL_BOUND_VIOLATED'
    END AS variational_validation
FROM experiments
WHERE optimized_energy IS NOT NULL
  AND exact_energy IS NOT NULL;

COMMIT;
