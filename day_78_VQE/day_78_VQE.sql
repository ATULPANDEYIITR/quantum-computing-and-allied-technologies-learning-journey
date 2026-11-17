-- ============================================================
-- VARIATIONAL QUANTUM EIGENSOLVER
-- PostgreSQL experiment management and optimization workflow
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;

SET search_path TO quantum_lab, public;

-- ------------------------------------------------------------
-- 1. Domain types
-- ------------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'created',
    'running',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE execution_backend AS ENUM (
    'statevector_simulator',
    'shot_simulator',
    'quantum_hardware'
);

CREATE TYPE measurement_status AS ENUM (
    'pending',
    'completed',
    'failed'
);

CREATE TYPE optimization_method AS ENUM (
    'gradient_descent',
    'spsa',
    'cobyla',
    'adam'
);

CREATE TYPE pauli_operator AS ENUM (
    'I', 'X', 'Y', 'Z'
);

-- ------------------------------------------------------------
-- 2. Organizations and users
-- ------------------------------------------------------------

CREATE TABLE research_organizations (
    organization_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_name VARCHAR(150) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE researchers (
    researcher_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id BIGINT NOT NULL
        REFERENCES research_organizations(organization_id),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_researchers_organization
    ON researchers(organization_id);

-- ------------------------------------------------------------
-- 3. Quantum computing systems
-- ------------------------------------------------------------

CREATE TABLE quantum_backends (
    backend_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    backend_name VARCHAR(150) NOT NULL UNIQUE,
    backend_type execution_backend NOT NULL,
    maximum_qubits INTEGER NOT NULL CHECK (maximum_qubits > 0),
    supports_shots BOOLEAN NOT NULL DEFAULT TRUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    average_execution_time_ms NUMERIC(12,3)
        CHECK (
            average_execution_time_ms IS NULL
            OR average_execution_time_ms >= 0
        ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 4. Quantum experiments
-- ------------------------------------------------------------

CREATE TABLE quantum_experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    organization_id BIGINT NOT NULL
        REFERENCES research_organizations(organization_id),

    researcher_id BIGINT NOT NULL
        REFERENCES researchers(researcher_id),

    backend_id BIGINT NOT NULL
        REFERENCES quantum_backends(backend_id),

    experiment_name VARCHAR(200) NOT NULL,

    algorithm_name VARCHAR(50) NOT NULL DEFAULT 'VQE'
        CHECK (algorithm_name = 'VQE'),

    status experiment_status NOT NULL DEFAULT 'created',

    number_of_qubits INTEGER NOT NULL
        CHECK (number_of_qubits > 0),

    ansatz_name VARCHAR(150) NOT NULL,

    ansatz_depth INTEGER NOT NULL
        CHECK (ansatz_depth > 0),

    optimization_algorithm optimization_method NOT NULL,

    maximum_iterations INTEGER NOT NULL
        CHECK (maximum_iterations > 0),

    learning_rate NUMERIC(14,10) NOT NULL
        CHECK (learning_rate > 0),

    convergence_tolerance NUMERIC(18,14) NOT NULL
        CHECK (convergence_tolerance > 0),

    measurement_shots INTEGER NOT NULL DEFAULT 0
        CHECK (measurement_shots >= 0),

    initial_parameters JSONB NOT NULL DEFAULT '[]'::jsonb
        CHECK (jsonb_typeof(initial_parameters) = 'array'),

    optimized_parameters JSONB
        CHECK (
            optimized_parameters IS NULL
            OR jsonb_typeof(optimized_parameters) = 'array'
        ),

    final_energy NUMERIC(20,14),

    exact_ground_energy NUMERIC(20,14),

    execution_error NUMERIC(20,14),

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),

    CHECK (
        status <> 'completed'
        OR (
            final_energy IS NOT NULL
            AND optimized_parameters IS NOT NULL
            AND started_at IS NOT NULL
            AND completed_at IS NOT NULL
        )
    ),

    UNIQUE (experiment_id, number_of_qubits)
);

CREATE INDEX idx_experiments_status
    ON quantum_experiments(status, created_at DESC);

CREATE INDEX idx_experiments_researcher
    ON quantum_experiments(researcher_id, created_at DESC);

CREATE INDEX idx_experiments_parameters
    ON quantum_experiments USING GIN(optimized_parameters);

-- ------------------------------------------------------------
-- 5. Hamiltonian definition
-- ------------------------------------------------------------

CREATE TABLE hamiltonians (
    hamiltonian_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id)
        ON DELETE CASCADE,

    hamiltonian_name VARCHAR(150) NOT NULL,

    physical_system VARCHAR(150) NOT NULL,

    reference_energy NUMERIC(20,14),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, hamiltonian_name)
);

CREATE TABLE hamiltonian_terms (
    term_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    hamiltonian_id BIGINT NOT NULL
        REFERENCES hamiltonians(hamiltonian_id)
        ON DELETE CASCADE,

    coefficient NUMERIC(20,14) NOT NULL,

    pauli_string TEXT NOT NULL
        CHECK (
            pauli_string <> ''
            AND pauli_string !~ '[^IXYZ]'
        ),

    CHECK (length(pauli_string) > 0),

    UNIQUE (hamiltonian_id, pauli_string)
);

CREATE INDEX idx_hamiltonian_terms_parent
    ON hamiltonian_terms(hamiltonian_id);

-- ------------------------------------------------------------
-- 6. Optimization iteration history
-- ------------------------------------------------------------

CREATE TABLE optimization_iterations (
    iteration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id)
        ON DELETE CASCADE,

    iteration_number INTEGER NOT NULL
        CHECK (iteration_number >= 0),

    parameter_vector JSONB NOT NULL
        CHECK (jsonb_typeof(parameter_vector) = 'array'),

    energy NUMERIC(20,14) NOT NULL,

    gradient_norm NUMERIC(20,14)
        CHECK (gradient_norm IS NULL OR gradient_norm >= 0),

    learning_rate NUMERIC(14,10),

    evaluation_type VARCHAR(30) NOT NULL DEFAULT 'exact'
        CHECK (evaluation_type IN ('exact', 'sampled')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, iteration_number)
);

CREATE INDEX idx_iterations_energy
    ON optimization_iterations(experiment_id, energy);

-- ------------------------------------------------------------
-- 7. Measurement records
-- ------------------------------------------------------------

CREATE TABLE measurement_batches (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiments(experiment_id)
        ON DELETE CASCADE,

    iteration_id BIGINT
        REFERENCES optimization_iterations(iteration_id)
        ON DELETE SET NULL,

    observable pauli_operator NOT NULL,

    coefficient NUMERIC(20,14) NOT NULL,

    shots INTEGER NOT NULL CHECK (shots > 0),

    positive_counts INTEGER NOT NULL,

    negative_counts INTEGER NOT NULL,

    measured_expectation NUMERIC(14,10),

    status measurement_status NOT NULL DEFAULT 'pending',

    executed_at TIMESTAMPTZ,

    CHECK (positive_counts >= 0),

    CHECK (negative_counts >= 0),

    CHECK (positive_counts + negative_counts <= shots),

    CHECK (
        measured_expectation IS NULL
        OR measured_expectation BETWEEN -1 AND 1
    ),

    CHECK (
        status <> 'completed'
        OR (
            positive_counts + negative_counts = shots
            AND measured_expectation IS NOT NULL
            AND executed_at IS NOT NULL
        )
    )
);

CREATE INDEX idx_measurements_experiment
    ON measurement_batches(experiment_id, status);

-- ------------------------------------------------------------
-- 8. Experiment validation and lifecycle
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_experiment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    backend_qubits INTEGER;
    backend_enabled BOOLEAN;
    backend_kind execution_backend;
    researcher_organization BIGINT;
BEGIN
    SELECT maximum_qubits, active, backend_type
    INTO backend_qubits, backend_enabled, backend_kind
    FROM quantum_backends
    WHERE backend_id = NEW.backend_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Quantum backend does not exist.';
    END IF;

    IF NOT backend_enabled THEN
        RAISE EXCEPTION 'Quantum backend is inactive.';
    END IF;

    IF NEW.number_of_qubits > backend_qubits THEN
        RAISE EXCEPTION
            'Requested % qubits; backend supports %.',
            NEW.number_of_qubits,
            backend_qubits;
    END IF;

    SELECT organization_id
    INTO researcher_organization
    FROM researchers
    WHERE researcher_id = NEW.researcher_id
      AND active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Researcher is inactive or unavailable.';
    END IF;

    IF researcher_organization <> NEW.organization_id THEN
        RAISE EXCEPTION
            'Researcher does not belong to experiment organization.';
    END IF;

    IF NEW.measurement_shots = 0
       AND backend_kind <> 'statevector_simulator' THEN
        RAISE EXCEPTION
            'Zero-shot execution requires a statevector simulator.';
    END IF;

    IF NEW.measurement_shots > 0
       AND NOT EXISTS (
           SELECT 1
           FROM quantum_backends
           WHERE backend_id = NEW.backend_id
             AND supports_shots = TRUE
       ) THEN
        RAISE EXCEPTION
            'Selected backend does not support shot measurements.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment
BEFORE INSERT OR UPDATE OF
    backend_id,
    researcher_id,
    organization_id,
    number_of_qubits,
    measurement_shots
ON quantum_experiments
FOR EACH ROW
EXECUTE FUNCTION validate_experiment();

-- ------------------------------------------------------------
-- 9. Experiment state transition enforcement
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'created'
       AND NEW.status IN ('running', 'cancelled', 'failed') THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'running'
       AND NEW.status IN ('completed', 'failed', 'cancelled') THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid experiment transition: % -> %',
        OLD.status,
        NEW.status;
END;
$$;

CREATE TRIGGER trg_experiment_transition
BEFORE UPDATE OF status
ON quantum_experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ------------------------------------------------------------
-- 10. Iteration integrity
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_iteration()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
BEGIN
    SELECT status
    INTO current_status
    FROM quantum_experiments
    WHERE experiment_id = NEW.experiment_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist.';
    END IF;

    IF current_status <> 'running' THEN
        RAISE EXCEPTION
            'Iterations can only be recorded for running experiments.';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_iteration
BEFORE INSERT
ON optimization_iterations
FOR EACH ROW
EXECUTE FUNCTION validate_iteration();

-- ------------------------------------------------------------
-- 11. Measurement expectation calculation
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION calculate_measurement_expectation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.positive_counts + NEW.negative_counts = NEW.shots THEN
        NEW.measured_expectation :=
            (
                NEW.positive_counts::NUMERIC -
                NEW.negative_counts::NUMERIC
            ) / NEW.shots;

        IF NEW.status = 'completed' THEN
            NEW.executed_at := COALESCE(
                NEW.executed_at,
                CURRENT_TIMESTAMP
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_measurement_expectation
BEFORE INSERT OR UPDATE
ON measurement_batches
FOR EACH ROW
EXECUTE FUNCTION calculate_measurement_expectation();

-- ------------------------------------------------------------
-- 12. Start experiment procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE quantum_experiments
    SET status = 'running',
        started_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id
      AND status = 'created';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment unavailable or cannot be started.';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 13. Complete experiment procedure
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_experiment(
    p_experiment_id BIGINT,
    p_final_energy NUMERIC,
    p_parameters JSONB,
    p_exact_energy NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_final_energy IS NULL
       OR p_exact_energy IS NULL
       OR jsonb_typeof(p_parameters) <> 'array' THEN
        RAISE EXCEPTION 'Invalid experiment result.';
    END IF;

    UPDATE quantum_experiments
    SET status = 'completed',
        final_energy = p_final_energy,
        exact_ground_energy = p_exact_energy,
        execution_error = ABS(
            p_final_energy - p_exact_energy
        ),
        optimized_parameters = p_parameters,
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = p_experiment_id
      AND status = 'running';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Only running experiments can be completed.';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 14. Experiment reporting views
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_overview AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.algorithm_name,
    e.status,
    r.full_name AS researcher,
    o.organization_name,
    b.backend_name,
    b.backend_type,
    e.number_of_qubits,
    e.ansatz_name,
    e.ansatz_depth,
    e.optimization_algorithm,
    e.final_energy,
    e.exact_ground_energy,
    e.execution_error,
    e.measurement_shots,
    e.created_at,
    e.completed_at
FROM quantum_experiments e
JOIN researchers r
    ON r.researcher_id = e.researcher_id
JOIN research_organizations o
    ON o.organization_id = e.organization_id
JOIN quantum_backends b
    ON b.backend_id = e.backend_id;

CREATE OR REPLACE VIEW experiment_iteration_summary AS
SELECT
    experiment_id,
    COUNT(*) AS total_iterations,
    MIN(energy) AS lowest_observed_energy,
    MAX(energy) AS highest_observed_energy,
    AVG(energy) AS average_energy,
    MIN(gradient_norm) AS minimum_gradient_norm
FROM optimization_iterations
GROUP BY experiment_id;

-- ------------------------------------------------------------
-- 15. Sample organizations, users and backends
-- ------------------------------------------------------------

INSERT INTO research_organizations(organization_name)
VALUES
    ('Quantum Research Laboratory'),
    ('Computational Chemistry Group');

INSERT INTO researchers(
    organization_id,
    full_name,
    email
)
VALUES
    (
        1,
        'Dr. Ananya Sharma',
        'ananya@quantum-lab.example'
    ),
    (
        1,
        'Dr. Rahul Verma',
        'rahul@quantum-lab.example'
    ),
    (
        2,
        'Dr. Meera Singh',
        'meera@chemistry.example'
    );

INSERT INTO quantum_backends(
    backend_name,
    backend_type,
    maximum_qubits,
    supports_shots,
    average_execution_time_ms
)
VALUES
    (
        'Local Statevector Engine',
        'statevector_simulator',
        20,
        TRUE,
        1.500
    ),
    (
        'Finite Shot Simulator',
        'shot_simulator',
        12,
        TRUE,
        5.250
    ),
    (
        'Unavailable Hardware',
        'quantum_hardware',
        5,
        TRUE,
        NULL
    );

-- ------------------------------------------------------------
-- 16. Experiment records
-- ------------------------------------------------------------

INSERT INTO quantum_experiments(
    organization_id,
    researcher_id,
    backend_id,
    experiment_name,
    number_of_qubits,
    ansatz_name,
    ansatz_depth,
    optimization_algorithm,
    maximum_iterations,
    learning_rate,
    convergence_tolerance,
    measurement_shots,
    initial_parameters
)
VALUES
    (
        1, 1, 1,
        'Single Qubit Ground State',
        1, 'Ry Ansatz', 1,
        'gradient_descent',
        300, 0.15, 0.0000000001,
        0, '[0.5]'
    ),
    (
        1, 2, 2,
        'Finite Shot VQE Experiment',
        1, 'Ry Ansatz', 1,
        'spsa',
        200, 0.10, 0.000001,
        1000, '[0.3]'
    ),
    (
        2, 3, 1,
        'Molecular Hamiltonian Prototype',
        1, 'Ry Ansatz', 1,
        'adam',
        400, 0.05, 0.0000001,
        0, '[0.8]'
    );

-- ------------------------------------------------------------
-- 17. Hamiltonian definitions
-- H = -Z - 0.5X
-- ------------------------------------------------------------

INSERT INTO hamiltonians(
    experiment_id,
    hamiltonian_name,
    physical_system,
    reference_energy
)
VALUES
    (
        1,
        'Single Qubit Hamiltonian',
        'Two-level quantum system',
        -1.11803398874989
    ),
    (
        2,
        'Sampled Hamiltonian',
        'Two-level quantum system',
        -1.11803398874989
    ),
    (
        3,
        'Prototype Hamiltonian',
        'Simplified molecular model',
        -1.11803398874989
    );

INSERT INTO hamiltonian_terms(
    hamiltonian_id,
    coefficient,
    pauli_string
)
VALUES
    (1, -1.0, 'Z'),
    (1, -0.5, 'X'),
    (2, -1.0, 'Z'),
    (2, -0.5, 'X'),
    (3, -1.0, 'Z'),
    (3, -0.5, 'X');

-- ------------------------------------------------------------
-- 18. Start first experiment
-- ------------------------------------------------------------

CALL start_experiment(1);

-- ------------------------------------------------------------
-- 19. Store optimization iterations
-- ------------------------------------------------------------

INSERT INTO optimization_iterations(
    experiment_id,
    iteration_number,
    parameter_vector,
    energy,
    gradient_norm,
    learning_rate,
    evaluation_type
)
VALUES
    (1, 0, '[0.5]', -1.030312, 0.575311, 0.15, 'exact'),
    (1, 1, '[0.586296]', -1.080000, 0.490000, 0.15, 'exact'),
    (1, 2, '[0.659796]', -1.100000, 0.400000, 0.15, 'exact'),
    (1, 3, '[0.719796]', -1.110000, 0.250000, 0.15, 'exact');

-- ------------------------------------------------------------
-- 20. Measurement batches
-- ------------------------------------------------------------

INSERT INTO measurement_batches(
    experiment_id,
    observable,
    coefficient,
    shots,
    positive_counts,
    negative_counts,
    status
)
VALUES
    (2, 'X', -0.5, 1000, 900, 100, 'completed'),
    (2, 'Z', -1.0, 1000, 850, 150, 'completed');

-- ------------------------------------------------------------
-- 21. Complete first experiment
-- ------------------------------------------------------------

CALL complete_experiment(
    1,
    -1.11803398874989,
    '[0.46364760900081]',
    -1.11803398874989
);

-- ------------------------------------------------------------
-- 22. Retrieval: experiment overview
-- ------------------------------------------------------------

SELECT *
FROM experiment_overview
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- 23. Retrieval: Hamiltonian terms
-- ------------------------------------------------------------

SELECT
    h.hamiltonian_name,
    t.coefficient,
    t.pauli_string
FROM hamiltonians h
JOIN hamiltonian_terms t
    ON t.hamiltonian_id = h.hamiltonian_id
WHERE h.experiment_id = 1
ORDER BY t.term_id;

-- ------------------------------------------------------------
-- 24. Aggregation: iteration statistics
-- ------------------------------------------------------------

SELECT *
FROM experiment_iteration_summary
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- 25. Evaluation: best energy by experiment
-- ------------------------------------------------------------

WITH ranked_iterations AS (
    SELECT
        experiment_id,
        iteration_number,
        energy,
        parameter_vector,
        ROW_NUMBER() OVER (
            PARTITION BY experiment_id
            ORDER BY energy ASC, iteration_number ASC
        ) AS energy_rank
    FROM optimization_iterations
)
SELECT
    experiment_id,
    iteration_number,
    energy,
    parameter_vector
FROM ranked_iterations
WHERE energy_rank = 1;

-- ------------------------------------------------------------
-- 26. Measurement evaluation
-- ------------------------------------------------------------

SELECT
    experiment_id,
    SUM(coefficient * measured_expectation) AS estimated_energy,
    SUM(shots) AS total_measurement_shots
FROM measurement_batches
WHERE status = 'completed'
GROUP BY experiment_id;

-- ------------------------------------------------------------
-- 27. Eligibility determination
-- ------------------------------------------------------------

SELECT
    e.experiment_id,
    e.experiment_name,
    CASE
        WHEN e.status = 'completed'
             AND e.final_energy IS NOT NULL
             AND e.optimized_parameters IS NOT NULL
        THEN TRUE
        ELSE FALSE
    END AS result_eligible,

    CASE
        WHEN e.status <> 'completed'
        THEN 'Experiment is not completed'
        WHEN e.final_energy IS NULL
        THEN 'Final energy missing'
        WHEN e.optimized_parameters IS NULL
        THEN 'Optimized parameters missing'
        ELSE 'Valid completed result'
    END AS eligibility_reason
FROM quantum_experiments e;

-- ------------------------------------------------------------
-- 28. Operational reporting
-- ------------------------------------------------------------

SELECT
    b.backend_name,
    COUNT(e.experiment_id) AS total_experiments,
    COUNT(*) FILTER (
        WHERE e.status = 'completed'
    ) AS completed_experiments,
    COUNT(*) FILTER (
        WHERE e.status = 'failed'
    ) AS failed_experiments,
    AVG(e.execution_error) AS average_energy_error
FROM quantum_backends b
LEFT JOIN quantum_experiments e
    ON e.backend_id = b.backend_id
GROUP BY b.backend_id, b.backend_name
ORDER BY total_experiments DESC;

-- ------------------------------------------------------------
-- 29. Failure-case validation
-- Execute this statement separately to test constraint rejection:
--
-- INSERT INTO hamiltonian_terms(
--     hamiltonian_id, coefficient, pauli_string
-- ) VALUES (1, 1.0, 'INVALID');
--
-- The CHECK constraint rejects the invalid Pauli string.
--
-- An attempt to complete a CREATED experiment directly also
-- fails because the state-transition trigger rejects it.
-- ------------------------------------------------------------

COMMIT;

-- ------------------------------------------------------------
-- 30. Example transactional rollback
--
-- Run separately when testing failure recovery:
--
-- BEGIN;
-- CALL start_experiment(2);
-- ROLLBACK;
--
-- Experiment 2 returns to its previous CREATED state.
-- ------------------------------------------------------------
