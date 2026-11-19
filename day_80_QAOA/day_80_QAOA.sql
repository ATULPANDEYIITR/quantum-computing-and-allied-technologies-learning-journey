-- ============================================================
-- QAOA EXPERIMENT MANAGEMENT AND ANALYTICS DATABASE
-- PostgreSQL 15+
--
-- Domain:
-- Graph optimization, QAOA circuits, Hamiltonians,
-- variational parameters, classical optimization,
-- quantum measurements, and experiment evaluation.
--
-- The schema separates:
-- 1. Graph definitions.
-- 2. QAOA experiment configurations.
-- 3. Circuit layers and parameters.
-- 4. Optimization iterations.
-- 5. Quantum measurement outcomes.
-- 6. Execution status and reproducibility.
-- 7. Experiment evaluation and reporting.
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS qaoa;

SET search_path TO qaoa, public;

-- ============================================================
-- ENUMERATIONS
-- ============================================================

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'QUEUED',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE optimization_method AS ENUM (
    'COORDINATE_SEARCH',
    'COBYLA',
    'NELDER_MEAD',
    'SPSA',
    'ADAM',
    'GRID_SEARCH'
);

CREATE TYPE measurement_source AS ENUM (
    'STATEVECTOR',
    'SIMULATOR',
    'QUANTUM_HARDWARE'
);

CREATE TYPE layer_type AS ENUM (
    'COST',
    'MIXER'
);

-- ============================================================
-- REPOSITORY OF GRAPH PROBLEMS
-- ============================================================

CREATE TABLE graphs (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_name VARCHAR(150) NOT NULL UNIQUE,

    vertex_count INTEGER NOT NULL
        CHECK (vertex_count BETWEEN 1 AND 100000),

    problem_type VARCHAR(40) NOT NULL DEFAULT 'MAX_CUT'
        CHECK (problem_type IN ('MAX_CUT')),

    is_weighted BOOLEAN NOT NULL DEFAULT FALSE,

    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE graph_edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES graphs(graph_id) ON DELETE CASCADE,

    source_vertex INTEGER NOT NULL,

    target_vertex INTEGER NOT NULL,

    weight NUMERIC(18, 8) NOT NULL DEFAULT 1.0
        CHECK (weight > 0),

    CHECK (source_vertex >= 0),
    CHECK (target_vertex >= 0),
    CHECK (source_vertex <> target_vertex),

    UNIQUE (graph_id, source_vertex, target_vertex)
);

-- ============================================================
-- GRAPH EDGE NORMALIZATION
--
-- A graph edge is undirected. Canonical endpoint ordering
-- prevents duplicate representations such as (0,1) and (1,0).
-- ============================================================

CREATE OR REPLACE FUNCTION validate_graph_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total_vertices INTEGER;
BEGIN
    SELECT vertex_count
    INTO total_vertices
    FROM graphs
    WHERE graph_id = NEW.graph_id;

    IF total_vertices IS NULL THEN
        RAISE EXCEPTION 'Graph does not exist: %', NEW.graph_id;
    END IF;

    IF NEW.source_vertex >= total_vertices
       OR NEW.target_vertex >= total_vertices THEN
        RAISE EXCEPTION
            'Edge endpoint exceeds graph vertex count';
    END IF;

    IF NEW.source_vertex > NEW.target_vertex THEN
        RAISE EXCEPTION
            'Normalize undirected edges: source must be less than target';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER graph_edge_validation
BEFORE INSERT OR UPDATE ON graph_edges
FOR EACH ROW
EXECUTE FUNCTION validate_graph_edge();

-- ============================================================
-- QAOA EXPERIMENTS
-- ============================================================

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_code VARCHAR(100) NOT NULL UNIQUE,

    graph_id BIGINT NOT NULL
        REFERENCES graphs(graph_id) ON DELETE RESTRICT,

    algorithm_name VARCHAR(50) NOT NULL DEFAULT 'QAOA'
        CHECK (algorithm_name = 'QAOA'),

    depth INTEGER NOT NULL
        CHECK (depth BETWEEN 1 AND 100),

    optimizer optimization_method NOT NULL,

    status experiment_status NOT NULL DEFAULT 'CREATED',

    random_seed BIGINT NOT NULL DEFAULT 42,

    shots INTEGER NOT NULL DEFAULT 1000
        CHECK (shots BETWEEN 1 AND 100000000),

    max_iterations INTEGER NOT NULL DEFAULT 100
        CHECK (max_iterations BETWEEN 1 AND 1000000),

    backend_name VARCHAR(150),

    backend_type measurement_source NOT NULL DEFAULT 'STATEVECTOR',

    created_by VARCHAR(150) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CHECK (
        completed_at IS NULL
        OR started_at IS NOT NULL
    ),

    CHECK (
        status <> 'COMPLETED'
        OR completed_at IS NOT NULL
    ),

    CHECK (
        status <> 'FAILED'
        OR failure_reason IS NOT NULL
    )
);

-- ============================================================
-- CIRCUIT LAYERS
--
-- Each QAOA layer contains a cost operation followed by
-- a mixer operation.
-- ============================================================

CREATE TABLE circuit_layers (
    layer_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    layer_number INTEGER NOT NULL
        CHECK (layer_number >= 0),

    operation layer_type NOT NULL,

    parameter_value NUMERIC(18, 12) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, layer_number, operation)
);

CREATE TABLE optimizer_iterations (
    iteration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    iteration_number INTEGER NOT NULL
        CHECK (iteration_number >= 0),

    expected_cut NUMERIC(20, 10) NOT NULL,

    objective_value NUMERIC(20, 10) NOT NULL,

    step_size NUMERIC(18, 12),

    gradient_norm NUMERIC(20, 12),

    accepted BOOLEAN NOT NULL DEFAULT TRUE,

    parameter_snapshot JSONB NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, iteration_number)
);

-- ============================================================
-- QUANTUM MEASUREMENT RECORDS
-- ============================================================

CREATE TABLE measurement_outcomes (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    bitstring VARCHAR(100000) NOT NULL,

    occurrence_count BIGINT NOT NULL
        CHECK (occurrence_count > 0),

    probability NUMERIC(18, 12)
        CHECK (probability BETWEEN 0 AND 1),

    cut_value NUMERIC(20, 8) NOT NULL
        CHECK (cut_value >= 0),

    source measurement_source NOT NULL,

    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (experiment_id, bitstring, source)
);

-- ============================================================
-- EXPERIMENT EVALUATION
-- ============================================================

CREATE TABLE experiment_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL UNIQUE
        REFERENCES experiments(experiment_id) ON DELETE CASCADE,

    classical_optimum NUMERIC(20, 8) NOT NULL
        CHECK (classical_optimum >= 0),

    quantum_expectation NUMERIC(20, 8) NOT NULL
        CHECK (quantum_expectation >= 0),

    approximation_ratio NUMERIC(18, 12) NOT NULL
        CHECK (approximation_ratio >= 0 AND approximation_ratio <= 1),

    best_observed_cut NUMERIC(20, 8) NOT NULL
        CHECK (best_observed_cut >= 0),

    total_measurements BIGINT NOT NULL
        CHECK (total_measurements > 0),

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PERFORMANCE INDEXES
-- ============================================================

CREATE INDEX idx_graph_edges_graph
ON graph_edges(graph_id);

CREATE INDEX idx_experiments_status_created
ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_graph
ON experiments(graph_id);

CREATE INDEX idx_circuit_layers_experiment
ON circuit_layers(experiment_id, layer_number);

CREATE INDEX idx_optimizer_iterations_history
ON optimizer_iterations(experiment_id, iteration_number);

CREATE INDEX idx_measurement_experiment_cut
ON measurement_outcomes(experiment_id, cut_value DESC);

CREATE INDEX idx_measurement_experiment_count
ON measurement_outcomes(experiment_id, occurrence_count DESC);

CREATE INDEX idx_experiment_metadata
ON experiments USING GIN(metadata);

-- ============================================================
-- EXPERIMENT STATE TRANSITION ENFORCEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION enforce_experiment_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'CREATED'
       AND NEW.status IN ('QUEUED', 'CANCELLED', 'FAILED') THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'QUEUED'
       AND NEW.status IN ('RUNNING', 'CANCELLED', 'FAILED') THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'RUNNING'
       AND NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION
        'Invalid experiment transition: % -> %',
        OLD.status,
        NEW.status;
END;
$$;

CREATE TRIGGER experiment_state_transition
BEFORE UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION enforce_experiment_transition();

-- ============================================================
-- EXPERIMENT TIMESTAMP MANAGEMENT
-- ============================================================

CREATE OR REPLACE FUNCTION maintain_experiment_timestamps()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'RUNNING' AND NEW.started_at IS NULL THEN
        NEW.started_at = CURRENT_TIMESTAMP;
    END IF;

    IF NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED') THEN
        NEW.completed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER experiment_timestamp_management
BEFORE INSERT OR UPDATE ON experiments
FOR EACH ROW
EXECUTE FUNCTION maintain_experiment_timestamps();

-- ============================================================
-- LAYER PARAMETER VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_circuit_layer()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    configured_depth INTEGER;
    current_status experiment_status;
BEGIN
    SELECT depth, status
    INTO configured_depth, current_status
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF current_status IS NULL THEN
        RAISE EXCEPTION 'Experiment does not exist';
    END IF;

    IF current_status <> 'CREATED' THEN
        RAISE EXCEPTION
            'Circuit configuration cannot change after submission';
    END IF;

    IF NEW.layer_number >= configured_depth THEN
        RAISE EXCEPTION
            'Layer number exceeds configured circuit depth';
    END IF;

    IF NEW.operation = 'COST'
       AND (
           NEW.parameter_value < 0
           OR NEW.parameter_value > PI()
       ) THEN
        RAISE EXCEPTION 'Invalid cost parameter';
    END IF;

    IF NEW.operation = 'MIXER'
       AND (
           NEW.parameter_value < 0
           OR NEW.parameter_value > PI() / 2
       ) THEN
        RAISE EXCEPTION 'Invalid mixer parameter';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER circuit_layer_validation
BEFORE INSERT OR UPDATE ON circuit_layers
FOR EACH ROW
EXECUTE FUNCTION validate_circuit_layer();

-- ============================================================
-- COMPUTE CLASSICAL CUT VALUE FROM A BITSTRING
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_cut_value(
    p_graph_id BIGINT,
    p_bitstring TEXT
)
RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    vertex_total INTEGER;
    result NUMERIC := 0;
    edge RECORD;
BEGIN
    SELECT vertex_count
    INTO vertex_total
    FROM graphs
    WHERE graph_id = p_graph_id;

    IF vertex_total IS NULL THEN
        RAISE EXCEPTION 'Graph not found';
    END IF;

    IF length(p_bitstring) <> vertex_total
       OR p_bitstring !~ '^[01]+$' THEN
        RAISE EXCEPTION 'Invalid measurement bitstring';
    END IF;

    FOR edge IN
        SELECT source_vertex, target_vertex, weight
        FROM graph_edges
        WHERE graph_id = p_graph_id
    LOOP
        IF substring(
            p_bitstring FROM edge.source_vertex + 1 FOR 1
        ) <> substring(
            p_bitstring FROM edge.target_vertex + 1 FOR 1
        ) THEN
            result := result + edge.weight;
        END IF;
    END LOOP;

    RETURN result;
END;
$$;

-- ============================================================
-- MEASUREMENT VALIDATION
-- ============================================================

CREATE OR REPLACE FUNCTION validate_measurement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    selected_graph BIGINT;
    calculated_value NUMERIC;
    vertex_total INTEGER;
BEGIN
    SELECT graph_id
    INTO selected_graph
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF selected_graph IS NULL THEN
        RAISE EXCEPTION 'Experiment not found';
    END IF;

    SELECT vertex_count
    INTO vertex_total
    FROM graphs
    WHERE graph_id = selected_graph;

    IF length(NEW.bitstring) <> vertex_total
       OR NEW.bitstring !~ '^[01]+$' THEN
        RAISE EXCEPTION 'Invalid measurement bitstring';
    END IF;

    calculated_value := calculate_cut_value(
        selected_graph,
        NEW.bitstring
    );

    IF abs(calculated_value - NEW.cut_value) > 0.00000001 THEN
        RAISE EXCEPTION
            'Measurement cut value does not match graph objective';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER measurement_validation
BEFORE INSERT OR UPDATE ON measurement_outcomes
FOR EACH ROW
EXECUTE FUNCTION validate_measurement();

-- ============================================================
-- REUSABLE EXPERIMENT SUBMISSION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE submit_experiment(
    p_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    current_status experiment_status;
    configured_depth INTEGER;
    actual_layers INTEGER;
BEGIN
    SELECT status, depth
    INTO current_status, configured_depth
    FROM experiments
    WHERE experiment_id = p_experiment_id
    FOR UPDATE;

    IF current_status IS NULL THEN
        RAISE EXCEPTION 'Experiment not found';
    END IF;

    IF current_status <> 'CREATED' THEN
        RAISE EXCEPTION 'Only CREATED experiments can be submitted';
    END IF;

    SELECT COUNT(*)
    INTO actual_layers
    FROM circuit_layers
    WHERE experiment_id = p_experiment_id
      AND operation = 'COST';

    IF actual_layers <> configured_depth THEN
        RAISE EXCEPTION
            'Missing cost circuit layers';
    END IF;

    SELECT COUNT(*)
    INTO actual_layers
    FROM circuit_layers
    WHERE experiment_id = p_experiment_id
      AND operation = 'MIXER';

    IF actual_layers <> configured_depth THEN
        RAISE EXCEPTION
            'Missing mixer circuit layers';
    END IF;

    UPDATE experiments
    SET status = 'QUEUED'
    WHERE experiment_id = p_experiment_id;
END;
$$;

-- ============================================================
-- ELIGIBILITY AND QUALITY VIEW
-- ============================================================

CREATE OR REPLACE VIEW experiment_readiness AS
SELECT
    e.experiment_id,
    e.experiment_code,
    e.status,
    e.depth,
    g.graph_name,
    g.vertex_count,

    COUNT(
        DISTINCT CASE
            WHEN cl.operation = 'COST'
            THEN cl.layer_number
        END
    ) AS configured_cost_layers,

    COUNT(
        DISTINCT CASE
            WHEN cl.operation = 'MIXER'
            THEN cl.layer_number
        END
    ) AS configured_mixer_layers,

    CASE
        WHEN COUNT(
            DISTINCT CASE
                WHEN cl.operation = 'COST'
                THEN cl.layer_number
            END
        ) = e.depth
        AND COUNT(
            DISTINCT CASE
                WHEN cl.operation = 'MIXER'
                THEN cl.layer_number
            END
        ) = e.depth
        THEN TRUE
        ELSE FALSE
    END AS circuit_ready

FROM experiments e
JOIN graphs g
    ON g.graph_id = e.graph_id

LEFT JOIN circuit_layers cl
    ON cl.experiment_id = e.experiment_id

GROUP BY
    e.experiment_id,
    e.experiment_code,
    e.status,
    e.depth,
    g.graph_name,
    g.vertex_count;

-- ============================================================
-- EXPERIMENT PERFORMANCE REPORT
-- ============================================================

CREATE OR REPLACE VIEW experiment_performance AS
SELECT
    e.experiment_code,
    e.status,
    g.graph_name,
    e.depth,
    e.optimizer,
    evaluation.classical_optimum,
    evaluation.quantum_expectation,
    evaluation.approximation_ratio,
    evaluation.best_observed_cut,
    evaluation.total_measurements,

    CASE
        WHEN evaluation.classical_optimum > 0
        THEN ROUND(
            100 * evaluation.approximation_ratio,
            2
        )
        ELSE 100
    END AS approximation_percentage,

    e.created_at,
    e.completed_at

FROM experiments e

JOIN graphs g
    ON g.graph_id = e.graph_id

LEFT JOIN experiment_evaluations evaluation
    ON evaluation.experiment_id = e.experiment_id;

-- ============================================================
-- SAMPLE GRAPH: FIVE-EDGE MAX-CUT INSTANCE
-- ============================================================

INSERT INTO graphs (
    graph_name,
    vertex_count,
    problem_type,
    is_weighted,
    description
)
VALUES (
    'QAOA-FOUR-VERTEX-MAXCUT',
    4,
    'MAX_CUT',
    FALSE,
    'Four-vertex graph with five unit-weight edges.'
);

INSERT INTO graph_edges (
    graph_id,
    source_vertex,
    target_vertex,
    weight
)
SELECT
    graph_id,
    edge.source_vertex,
    edge.target_vertex,
    edge.weight
FROM graphs
CROSS JOIN (
    VALUES
        (0, 1, 1.0::NUMERIC),
        (0, 2, 1.0::NUMERIC),
        (1, 2, 1.0::NUMERIC),
        (1, 3, 1.0::NUMERIC),
        (2, 3, 1.0::NUMERIC)
) AS edge(source_vertex, target_vertex, weight)
WHERE graph_name = 'QAOA-FOUR-VERTEX-MAXCUT';

-- ============================================================
-- CREATE EXPERIMENT
-- ============================================================

INSERT INTO experiments (
    experiment_code,
    graph_id,
    depth,
    optimizer,
    status,
    random_seed,
    shots,
    max_iterations,
    backend_name,
    backend_type,
    created_by,
    metadata
)
SELECT
    'QAOA-MAXCUT-EXP-001',
    graph_id,
    1,
    'COORDINATE_SEARCH',
    'CREATED',
    42,
    2000,
    100,
    'Local-Statevector-Simulator',
    'STATEVECTOR',
    'research-engineering',
    jsonb_build_object(
        'problem', 'MAX_CUT',
        'objective', 'maximize expected cut value',
        'initial_gamma', 0.7,
        'initial_beta', 0.3
    )
FROM graphs
WHERE graph_name = 'QAOA-FOUR-VERTEX-MAXCUT';

-- ============================================================
-- CONFIGURE P=1 CIRCUIT
-- ============================================================

INSERT INTO circuit_layers (
    experiment_id,
    layer_number,
    operation,
    parameter_value
)
SELECT
    experiment_id,
    0,
    'COST',
    0.7
FROM experiments
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

INSERT INTO circuit_layers (
    experiment_id,
    layer_number,
    operation,
    parameter_value
)
SELECT
    experiment_id,
    0,
    'MIXER',
    0.3
FROM experiments
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

-- ============================================================
-- DEMONSTRATE EXPERIMENT SUBMISSION
-- ============================================================

CALL submit_experiment(
    (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_code = 'QAOA-MAXCUT-EXP-001'
    )
);

-- Simulate the execution service starting the experiment.
UPDATE experiments
SET status = 'RUNNING'
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

-- ============================================================
-- RECORD OPTIMIZATION HISTORY
-- ============================================================

INSERT INTO optimizer_iterations (
    experiment_id,
    iteration_number,
    expected_cut,
    objective_value,
    step_size,
    accepted,
    parameter_snapshot
)
SELECT
    experiment_id,
    iteration_number,
    expected_cut,
    expected_cut,
    step_size,
    accepted,
    parameters
FROM experiments
CROSS JOIN (
    VALUES
        (
            0,
            2.1000000000::NUMERIC,
            0.1500000000::NUMERIC,
            TRUE,
            '{"gamma":[0.7],"beta":[0.3]}'::JSONB
        ),
        (
            1,
            2.3500000000::NUMERIC,
            0.1500000000::NUMERIC,
            TRUE,
            '{"gamma":[0.85],"beta":[0.3]}'::JSONB
        ),
        (
            2,
            2.4800000000::NUMERIC,
            0.0750000000::NUMERIC,
            TRUE,
            '{"gamma":[0.85],"beta":[0.375]}'::JSONB
        ),
        (
            3,
            2.4800000000::NUMERIC,
            0.0375000000::NUMERIC,
            FALSE,
            '{"gamma":[0.85],"beta":[0.375]}'::JSONB
        )
) AS iteration(
    iteration_number,
    expected_cut,
    step_size,
    accepted,
    parameters
)
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

-- ============================================================
-- RECORD MEASUREMENT OUTCOMES
--
-- Bitstrings use vertex order 0,1,2,3.
-- These records represent an illustrative measurement sample.
-- ============================================================

INSERT INTO measurement_outcomes (
    experiment_id,
    bitstring,
    occurrence_count,
    probability,
    cut_value,
    source
)
SELECT
    experiment_id,
    measurement.bitstring,
    measurement.occurrences,
    measurement.probability,
    calculate_cut_value(graph_id, measurement.bitstring),
    'STATEVECTOR'
FROM experiments
CROSS JOIN (
    VALUES
        ('0101', 520, 0.260000000000::NUMERIC),
        ('1010', 490, 0.245000000000::NUMERIC),
        ('0110', 350, 0.175000000000::NUMERIC),
        ('1001', 340, 0.170000000000::NUMERIC),
        ('0000', 150, 0.075000000000::NUMERIC),
        ('1111', 150, 0.075000000000::NUMERIC)
) AS measurement(bitstring, occurrences, probability)
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

-- ============================================================
-- CALCULATE CLASSICAL OPTIMUM
--
-- Exhaustive enumeration is suitable only for small graphs.
-- ============================================================

WITH RECURSIVE assignments AS (
    SELECT
        graph_id,
        vertex_count,
        0::BIGINT AS state,
        0::INTEGER AS position,
        ''::TEXT AS bitstring
    FROM graphs
    WHERE graph_name = 'QAOA-FOUR-VERTEX-MAXCUT'

    UNION ALL

    SELECT
        graph_id,
        vertex_count,
        state,
        position + 1,
        bitstring || bit
    FROM assignments
    CROSS JOIN (
        VALUES ('0'::TEXT), ('1'::TEXT)
    ) AS bits(bit)
    WHERE position < vertex_count
),
completed_assignments AS (
    SELECT
        graph_id,
        bitstring,
        calculate_cut_value(graph_id, bitstring) AS cut_value
    FROM assignments
    WHERE position = vertex_count
),
optimum AS (
    SELECT
        graph_id,
        MAX(cut_value) AS maximum_cut
    FROM completed_assignments
    GROUP BY graph_id
)
SELECT
    completed_assignments.bitstring,
    completed_assignments.cut_value,
    optimum.maximum_cut
FROM completed_assignments
JOIN optimum
    USING (graph_id)
WHERE completed_assignments.cut_value = optimum.maximum_cut
ORDER BY bitstring;

-- ============================================================
-- COMPLETE EXPERIMENT
-- ============================================================

UPDATE experiments
SET status = 'COMPLETED'
WHERE experiment_code = 'QAOA-MAXCUT-EXP-001';

-- ============================================================
-- EVALUATION RECORD
-- ============================================================

INSERT INTO experiment_evaluations (
    experiment_id,
    classical_optimum,
    quantum_expectation,
    approximation_ratio,
    best_observed_cut,
    total_measurements
)
SELECT
    e.experiment_id,
    4.0,
    2.48,
    0.62,
    MAX(m.cut_value),
    SUM(m.occurrence_count)
FROM experiments e
JOIN measurement_outcomes m
    ON m.experiment_id = e.experiment_id
WHERE e.experiment_code = 'QAOA-MAXCUT-EXP-001'
GROUP BY e.experiment_id;

-- ============================================================
-- VALIDATION QUERY 1: GRAPH STRUCTURE
-- ============================================================

SELECT
    g.graph_name,
    g.vertex_count,
    COUNT(e.edge_id) AS edge_count,
    SUM(e.weight) AS total_edge_weight
FROM graphs g
LEFT JOIN graph_edges e
    ON e.graph_id = g.graph_id
GROUP BY g.graph_id, g.graph_name, g.vertex_count;

-- ============================================================
-- VALIDATION QUERY 2: EXPERIMENT READINESS
-- ============================================================

SELECT *
FROM experiment_readiness
ORDER BY experiment_id;

-- ============================================================
-- VALIDATION QUERY 3: CIRCUIT PARAMETERS
-- ============================================================

SELECT
    experiment_id,
    layer_number,
    operation,
    parameter_value
FROM circuit_layers
ORDER BY experiment_id, layer_number, operation;

-- ============================================================
-- VALIDATION QUERY 4: PARAMETER OPTIMIZATION HISTORY
-- ============================================================

SELECT
    e.experiment_code,
    i.iteration_number,
    i.expected_cut,
    i.step_size,
    i.accepted,
    i.parameter_snapshot
FROM optimizer_iterations i
JOIN experiments e
    ON e.experiment_id = i.experiment_id
ORDER BY e.experiment_code, i.iteration_number;

-- ============================================================
-- REPORT 1: MEASUREMENT DISTRIBUTION
-- ============================================================

SELECT
    e.experiment_code,
    m.bitstring,
    m.cut_value,
    m.occurrence_count,
    m.probability,
    ROUND(
        100 * m.occurrence_count /
        NULLIF(
            SUM(m.occurrence_count) OVER (
                PARTITION BY m.experiment_id
            ),
            0
        ),
        2
    ) AS observed_percentage
FROM measurement_outcomes m
JOIN experiments e
    ON e.experiment_id = m.experiment_id
ORDER BY
    m.experiment_id,
    m.occurrence_count DESC;

-- ============================================================
-- REPORT 2: APPROXIMATION PERFORMANCE
-- ============================================================

SELECT *
FROM experiment_performance
ORDER BY approximation_ratio DESC NULLS LAST;

-- ============================================================
-- REPORT 3: BEST OBSERVED SOLUTION
-- ============================================================

SELECT DISTINCT ON (m.experiment_id)
    e.experiment_code,
    m.bitstring,
    m.cut_value,
    m.occurrence_count
FROM measurement_outcomes m
JOIN experiments e
    ON e.experiment_id = m.experiment_id
ORDER BY
    m.experiment_id,
    m.cut_value DESC,
    m.occurrence_count DESC;

-- ============================================================
-- REPORT 4: OPTIMIZATION CONVERGENCE
-- ============================================================

SELECT
    experiment_id,
    MIN(expected_cut) AS minimum_expected_cut,
    MAX(expected_cut) AS best_expected_cut,
    COUNT(*) AS iterations,
    MAX(iteration_number) AS final_iteration,
    COUNT(*) FILTER (WHERE accepted) AS accepted_iterations
FROM optimizer_iterations
GROUP BY experiment_id;

-- ============================================================
-- REPORT 5: MEASUREMENT QUALITY
-- ============================================================

SELECT
    experiment_id,
    SUM(occurrence_count) AS total_shots,
    SUM(probability) AS total_recorded_probability,
    MIN(cut_value) AS minimum_cut,
    MAX(cut_value) AS maximum_cut,
    SUM(cut_value * occurrence_count)
        / NULLIF(SUM(occurrence_count), 0)
        AS empirical_expected_cut
FROM measurement_outcomes
GROUP BY experiment_id;

-- ============================================================
-- TRANSACTIONAL FAILURE-HANDLING EXAMPLE
--
-- This transaction intentionally attempts to submit an
-- incomplete circuit. The exception rolls back the transaction.
--
-- Run separately when testing failure behavior.
-- ============================================================

SAVEPOINT before_invalid_submission;

-- The following block uses an isolated exception handler.
-- Its failed submission does not affect the completed experiment.

DO $$
BEGIN
    BEGIN
        CALL submit_experiment(
            (
                SELECT experiment_id
                FROM experiments
                WHERE experiment_code = 'QAOA-MAXCUT-EXP-001'
            )
        );
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected submission rejection: %',
                SQLERRM;
    END;
END;
$$;

RELEASE SAVEPOINT before_invalid_submission;

-- ============================================================
-- EXPLICIT DATA-INTEGRITY CHECKS
-- ============================================================

DO $$
DECLARE
    total_probability NUMERIC;
    total_shots BIGINT;
    completed_count INTEGER;
BEGIN
    SELECT SUM(probability), SUM(occurrence_count)
    INTO total_probability, total_shots
    FROM measurement_outcomes
    WHERE experiment_id = (
        SELECT experiment_id
        FROM experiments
        WHERE experiment_code = 'QAOA-MAXCUT-EXP-001'
    );

    IF abs(total_probability - 1.0) > 0.000001 THEN
        RAISE EXCEPTION
            'Measurement probabilities do not sum to one';
    END IF;

    IF total_shots <> 2000 THEN
        RAISE EXCEPTION
            'Unexpected measurement shot count';
    END IF;

    SELECT COUNT(*)
    INTO completed_count
    FROM experiments
    WHERE experiment_code = 'QAOA-MAXCUT-EXP-001'
      AND status = 'COMPLETED';

    IF completed_count <> 1 THEN
        RAISE EXCEPTION
            'Experiment completion validation failed';
    END IF;

    RAISE NOTICE 'Database integrity checks passed';
END;
$$;

COMMIT;

-- ============================================================
-- OPERATIONAL QUERIES
-- ============================================================

-- Recent experiment executions:
SELECT
    experiment_code,
    status,
    backend_name,
    created_at,
    started_at,
    completed_at,
    failure_reason
FROM qaoa.experiments
ORDER BY created_at DESC;

-- Failed experiment diagnostics:
SELECT
    experiment_code,
    failure_reason,
    metadata
FROM qaoa.experiments
WHERE status = 'FAILED';

-- Highest-performing completed experiments:
SELECT
    experiment_code,
    graph_name,
    depth,
    optimizer,
    approximation_ratio,
    best_observed_cut
FROM qaoa.experiment_performance
WHERE status = 'COMPLETED'
ORDER BY approximation_ratio DESC;

-- Experiments awaiting submission:
SELECT *
FROM qaoa.experiment_readiness
WHERE status = 'CREATED'
  AND circuit_ready = TRUE;
