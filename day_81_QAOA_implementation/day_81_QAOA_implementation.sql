-- ============================================================
-- QAOA EXPERIMENT MANAGEMENT AND MAX-CUT OPTIMIZATION
-- PostgreSQL 14+
--
-- Models:
--   Graphs and weighted edges
--   Quantum optimization experiments
--   QAOA parameters and execution history
--   Statevector evaluations
--   Measurement outcomes
--   Classical benchmarks
--   Experiment eligibility and reporting
-- ============================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS qaoa;

SET search_path TO qaoa, public;

-- ------------------------------------------------------------
-- 1. Domain types
-- ------------------------------------------------------------

CREATE TYPE experiment_status AS ENUM (
    'CREATED',
    'VALIDATING',
    'RUNNING',
    'COMPLETED',
    'FAILED',
    'CANCELLED'
);

CREATE TYPE optimizer_type AS ENUM (
    'GRID_SEARCH',
    'COORDINATE_SEARCH',
    'COBYLA',
    'SPSA'
);

CREATE TYPE execution_backend AS ENUM (
    'STATEVECTOR_SIMULATOR',
    'SHOT_BASED_SIMULATOR',
    'QUANTUM_HARDWARE'
);

CREATE TYPE objective_type AS ENUM (
    'MAX_CUT'
);

-- ------------------------------------------------------------
-- 2. Optimization graphs
-- ------------------------------------------------------------

CREATE TABLE optimization_graphs (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name VARCHAR(150) NOT NULL UNIQUE,
    objective objective_type NOT NULL DEFAULT 'MAX_CUT',
    vertex_count INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_vertex_count
        CHECK (vertex_count BETWEEN 2 AND 1000)
);

CREATE TABLE graph_edges (
    edge_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL
        REFERENCES optimization_graphs(graph_id)
        ON DELETE CASCADE,

    source_vertex INTEGER NOT NULL,
    target_vertex INTEGER NOT NULL,
    weight NUMERIC(14,6) NOT NULL DEFAULT 1.0,

    CONSTRAINT valid_edge_vertices
        CHECK (source_vertex >= 0
           AND target_vertex >= 0
           AND source_vertex <> target_vertex),

    CONSTRAINT positive_edge_weight
        CHECK (weight > 0),

    CONSTRAINT unique_undirected_edge
        UNIQUE (graph_id, source_vertex, target_vertex)
);

CREATE INDEX idx_graph_edges_graph
    ON graph_edges(graph_id);

-- ------------------------------------------------------------
-- 3. Quantum optimization experiments
-- ------------------------------------------------------------

CREATE TABLE experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES optimization_graphs(graph_id),

    experiment_name VARCHAR(150) NOT NULL,
    status experiment_status NOT NULL DEFAULT 'CREATED',

    qaoa_depth INTEGER NOT NULL DEFAULT 1,
    optimizer optimizer_type NOT NULL DEFAULT 'GRID_SEARCH',
    backend execution_backend NOT NULL
        DEFAULT 'STATEVECTOR_SIMULATOR',

    gamma_steps INTEGER NOT NULL DEFAULT 40,
    beta_steps INTEGER NOT NULL DEFAULT 40,

    random_seed BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    failure_reason TEXT,

    CONSTRAINT positive_qaoa_depth
        CHECK (qaoa_depth BETWEEN 1 AND 100),

    CONSTRAINT valid_grid_resolution
        CHECK (gamma_steps >= 2 AND beta_steps >= 2),

    CONSTRAINT valid_completion_time
        CHECK (
            completed_at IS NULL
            OR started_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT unique_experiment_name
        UNIQUE (experiment_name)
);

CREATE INDEX idx_experiments_status
    ON experiments(status, created_at DESC);

CREATE INDEX idx_experiments_graph
    ON experiments(graph_id, created_at DESC);

-- ------------------------------------------------------------
-- 4. QAOA parameter evaluations
-- ------------------------------------------------------------

CREATE TABLE parameter_evaluations (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    evaluation_number BIGINT NOT NULL,
    layer_number INTEGER NOT NULL DEFAULT 1,

    gamma DOUBLE PRECISION NOT NULL,
    beta DOUBLE PRECISION NOT NULL,

    expected_cut DOUBLE PRECISION NOT NULL,
    state_norm DOUBLE PRECISION NOT NULL DEFAULT 1.0,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_evaluation_number
        CHECK (evaluation_number > 0),

    CONSTRAINT valid_layer_number
        CHECK (layer_number > 0),

    CONSTRAINT finite_parameters
        CHECK (
            gamma > '-Infinity'::DOUBLE PRECISION
            AND gamma < 'Infinity'::DOUBLE PRECISION
            AND beta > '-Infinity'::DOUBLE PRECISION
            AND beta < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT valid_expected_cut
        CHECK (
            expected_cut >= 0
            AND expected_cut < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT valid_state_norm
        CHECK (
            state_norm > 0
            AND state_norm < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT unique_evaluation_number
        UNIQUE (experiment_id, evaluation_number)
);

CREATE INDEX idx_evaluations_best
    ON parameter_evaluations(
        experiment_id,
        expected_cut DESC
    );

-- ------------------------------------------------------------
-- 5. Measurement outcomes
-- ------------------------------------------------------------

CREATE TABLE measurement_outcomes (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    bitstring VARCHAR(1000) NOT NULL,
    observed_cut DOUBLE PRECISION NOT NULL,
    occurrence_count BIGINT NOT NULL DEFAULT 1,

    probability DOUBLE PRECISION NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_occurrences
        CHECK (occurrence_count > 0),

    CONSTRAINT valid_probability
        CHECK (probability >= 0 AND probability <= 1),

    CONSTRAINT valid_observed_cut
        CHECK (
            observed_cut >= 0
            AND observed_cut < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT unique_measurement
        UNIQUE (experiment_id, bitstring)
);

CREATE INDEX idx_measurements_experiment
    ON measurement_outcomes(experiment_id);

-- ------------------------------------------------------------
-- 6. Classical benchmarks
-- ------------------------------------------------------------

CREATE TABLE classical_benchmarks (
    benchmark_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    graph_id BIGINT NOT NULL
        REFERENCES optimization_graphs(graph_id)
        ON DELETE CASCADE,

    algorithm_name VARCHAR(100) NOT NULL,
    optimum_value DOUBLE PRECISION NOT NULL,
    optimal_partition VARCHAR(1000),

    execution_time_ms NUMERIC(16,4),
    verified BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_benchmark_value
        CHECK (
            optimum_value >= 0
            AND optimum_value < 'Infinity'::DOUBLE PRECISION
        ),

    CONSTRAINT valid_benchmark_time
        CHECK (
            execution_time_ms IS NULL
            OR execution_time_ms >= 0
        )
);

CREATE INDEX idx_benchmarks_graph
    ON classical_benchmarks(graph_id, verified);

-- ------------------------------------------------------------
-- 7. Audit history
-- ------------------------------------------------------------

CREATE TABLE experiment_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,

    previous_status experiment_status,
    new_status experiment_status NOT NULL,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

CREATE INDEX idx_audit_experiment
    ON experiment_audit(experiment_id, changed_at DESC);

-- ------------------------------------------------------------
-- 8. Validate graph edge endpoints
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_graph_edge()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    vertex_limit INTEGER;
BEGIN
    SELECT vertex_count
    INTO vertex_limit
    FROM optimization_graphs
    WHERE graph_id = NEW.graph_id
    FOR SHARE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Graph % does not exist', NEW.graph_id;
    END IF;

    IF NEW.source_vertex >= vertex_limit
       OR NEW.target_vertex >= vertex_limit THEN
        RAISE EXCEPTION
            'Edge endpoints must be below vertex count %',
            vertex_limit;
    END IF;

    -- Canonical ordering prevents duplicate undirected edges.
    IF NEW.source_vertex > NEW.target_vertex THEN
        RAISE EXCEPTION
            'Store undirected edges with source_vertex < target_vertex';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_graph_edge
BEFORE INSERT OR UPDATE ON graph_edges
FOR EACH ROW
EXECUTE FUNCTION validate_graph_edge();

-- ------------------------------------------------------------
-- 9. Validate measurement bitstrings
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION validate_measurement()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    required_vertices INTEGER;
    computed_cut DOUBLE PRECISION;
    bit_value INTEGER;
    edge_record RECORD;
BEGIN
    SELECT g.vertex_count
    INTO required_vertices
    FROM experiments e
    JOIN optimization_graphs g
      ON g.graph_id = e.graph_id
    WHERE e.experiment_id = NEW.experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment does not exist';
    END IF;

    IF length(NEW.bitstring) <> required_vertices
       OR NEW.bitstring !~ '^[01]+$' THEN
        RAISE EXCEPTION
            'Invalid measurement bitstring: %',
            NEW.bitstring;
    END IF;

    computed_cut := 0;

    FOR edge_record IN
        SELECT ge.source_vertex,
               ge.target_vertex,
               ge.weight
        FROM graph_edges ge
        JOIN experiments e
          ON e.graph_id = ge.graph_id
        WHERE e.experiment_id = NEW.experiment_id
    LOOP
        IF substr(
            NEW.bitstring,
            edge_record.source_vertex + 1,
            1
        ) <> substr(
            NEW.bitstring,
            edge_record.target_vertex + 1,
            1
        ) THEN
            computed_cut :=
                computed_cut + edge_record.weight::DOUBLE PRECISION;
        END IF;
    END LOOP;

    IF abs(computed_cut - NEW.observed_cut) > 0.000001 THEN
        RAISE EXCEPTION
            'Reported cut % does not match calculated cut %',
            NEW.observed_cut,
            computed_cut;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_measurement
BEFORE INSERT OR UPDATE ON measurement_outcomes
FOR EACH ROW
EXECUTE FUNCTION validate_measurement();

-- ------------------------------------------------------------
-- 10. Record experiment status transitions
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_experiment_status()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        IF NOT (
            (OLD.status = 'CREATED'
                AND NEW.status IN ('VALIDATING', 'CANCELLED'))
            OR
            (OLD.status = 'VALIDATING'
                AND NEW.status IN ('RUNNING', 'FAILED', 'CANCELLED'))
            OR
            (OLD.status = 'RUNNING'
                AND NEW.status IN ('COMPLETED', 'FAILED', 'CANCELLED'))
        ) THEN
            RAISE EXCEPTION
                'Invalid experiment transition: % -> %',
                OLD.status,
                NEW.status;
        END IF;

        INSERT INTO experiment_audit (
            experiment_id,
            previous_status,
            new_status,
            reason
        )
        VALUES (
            NEW.experiment_id,
            OLD.status,
            NEW.status,
            NEW.failure_reason
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_experiment_status
AFTER UPDATE OF status ON experiments
FOR EACH ROW
EXECUTE FUNCTION audit_experiment_status();

-- ------------------------------------------------------------
-- 11. Eligibility determination
-- ------------------------------------------------------------

CREATE OR REPLACE FUNCTION check_experiment_eligibility(
    requested_experiment_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    explanation TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    experiment_record RECORD;
    edge_count BIGINT;
    vertex_count_value INTEGER;
BEGIN
    SELECT e.*, g.vertex_count
    INTO experiment_record
    FROM experiments e
    JOIN optimization_graphs g
      ON g.graph_id = e.graph_id
    WHERE e.experiment_id = requested_experiment_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Experiment not found'::TEXT;
        RETURN;
    END IF;

    SELECT count(*)
    INTO edge_count
    FROM graph_edges
    WHERE graph_id = experiment_record.graph_id;

    IF edge_count = 0 THEN
        RETURN QUERY
        SELECT FALSE, 'Graph has no edges'::TEXT;
        RETURN;
    END IF;

    IF experiment_record.vertex_count > 20
       AND experiment_record.backend = 'STATEVECTOR_SIMULATOR' THEN
        RETURN QUERY
        SELECT FALSE,
            'Exact statevector simulation exceeds configured vertex limit'
            ::TEXT;
        RETURN;
    END IF;

    IF experiment_record.status NOT IN ('CREATED', 'VALIDATING') THEN
        RETURN QUERY
        SELECT FALSE, 'Experiment is not eligible for execution'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Graph and experiment configuration are valid'::TEXT;
END;
$$;

-- ------------------------------------------------------------
-- 12. Start an experiment transactionally
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE start_experiment(
    requested_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility RECORD;
BEGIN
    SELECT *
    INTO eligibility
    FROM check_experiment_eligibility(requested_experiment_id);

    IF NOT eligibility.eligible THEN
        RAISE EXCEPTION
            'Experiment cannot start: %',
            eligibility.explanation;
    END IF;

    UPDATE experiments
    SET status = 'VALIDATING'
    WHERE experiment_id = requested_experiment_id
      AND status = 'CREATED';

    UPDATE experiments
    SET status = 'RUNNING',
        started_at = CURRENT_TIMESTAMP
    WHERE experiment_id = requested_experiment_id
      AND status = 'VALIDATING';
END;
$$;

-- ------------------------------------------------------------
-- 13. Complete an experiment
-- ------------------------------------------------------------

CREATE OR REPLACE PROCEDURE complete_experiment(
    requested_experiment_id BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    evaluation_count BIGINT;
BEGIN
    SELECT count(*)
    INTO evaluation_count
    FROM parameter_evaluations
    WHERE experiment_id = requested_experiment_id;

    IF evaluation_count = 0 THEN
        RAISE EXCEPTION
            'Cannot complete experiment without evaluations';
    END IF;

    UPDATE experiments
    SET status = 'COMPLETED',
        completed_at = CURRENT_TIMESTAMP
    WHERE experiment_id = requested_experiment_id
      AND status = 'RUNNING';

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Experiment must be RUNNING before completion';
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 14. Reporting views
-- ------------------------------------------------------------

CREATE OR REPLACE VIEW experiment_best_parameters AS
SELECT
    experiment_id,
    evaluation_number,
    layer_number,
    gamma,
    beta,
    expected_cut,
    state_norm,
    evaluated_at
FROM (
    SELECT
        pe.*,
        row_number() OVER (
            PARTITION BY experiment_id
            ORDER BY expected_cut DESC, evaluation_number
        ) AS ranking
    FROM parameter_evaluations pe
) ranked
WHERE ranking = 1;

CREATE OR REPLACE VIEW experiment_performance_report AS
SELECT
    e.experiment_id,
    e.experiment_name,
    e.status,
    g.graph_name,
    g.vertex_count,
    (
        SELECT count(*)
        FROM graph_edges ge
        WHERE ge.graph_id = g.graph_id
    ) AS edge_count,
    e.qaoa_depth,
    e.backend,
    bp.gamma,
    bp.beta,
    bp.expected_cut,
    cb.optimum_value AS classical_optimum,
    CASE
        WHEN cb.optimum_value > 0
        THEN bp.expected_cut / cb.optimum_value
        ELSE NULL
    END AS approximation_ratio,
    bp.evaluation_number
FROM experiments e
JOIN optimization_graphs g
    ON g.graph_id = e.graph_id
LEFT JOIN experiment_best_parameters bp
    ON bp.experiment_id = e.experiment_id
LEFT JOIN LATERAL (
    SELECT optimum_value
    FROM classical_benchmarks
    WHERE graph_id = g.graph_id
      AND verified = TRUE
    ORDER BY created_at DESC
    LIMIT 1
) cb ON TRUE;

-- ------------------------------------------------------------
-- 15. Sample graph
-- ------------------------------------------------------------

INSERT INTO optimization_graphs (
    graph_name,
    objective,
    vertex_count,
    description
)
VALUES (
    'six_vertex_network',
    'MAX_CUT',
    6,
    'Weighted network used for QAOA MaxCut benchmarking.'
);

INSERT INTO graph_edges (
    graph_id,
    source_vertex,
    target_vertex,
    weight
)
SELECT
    g.graph_id,
    edges.source_vertex,
    edges.target_vertex,
    edges.weight
FROM optimization_graphs g
CROSS JOIN (
    VALUES
        (0, 1, 1.0::NUMERIC),
        (0, 2, 1.0::NUMERIC),
        (0, 5, 1.0::NUMERIC),
        (1, 2, 1.0::NUMERIC),
        (1, 3, 1.0::NUMERIC),
        (2, 4, 1.0::NUMERIC),
        (3, 4, 1.0::NUMERIC),
        (3, 5, 1.0::NUMERIC),
        (4, 5, 1.0::NUMERIC)
) AS edges(source_vertex, target_vertex, weight)
WHERE g.graph_name = 'six_vertex_network';

-- ------------------------------------------------------------
-- 16. Sample experiments
-- ------------------------------------------------------------

INSERT INTO experiments (
    graph_id,
    experiment_name,
    status,
    qaoa_depth,
    optimizer,
    backend,
    gamma_steps,
    beta_steps
)
SELECT
    graph_id,
    'maxcut_qaoa_grid_search',
    'CREATED',
    1,
    'GRID_SEARCH',
    'STATEVECTOR_SIMULATOR',
    40,
    40
FROM optimization_graphs
WHERE graph_name = 'six_vertex_network';

INSERT INTO experiments (
    graph_id,
    experiment_name,
    status,
    qaoa_depth,
    optimizer,
    backend,
    gamma_steps,
    beta_steps,
    failure_reason
)
SELECT
    graph_id,
    'maxcut_failed_configuration',
    'FAILED',
    1,
    'GRID_SEARCH',
    'STATEVECTOR_SIMULATOR',
    40,
    40,
    'Demonstration of a recorded failed experiment.'
FROM optimization_graphs
WHERE graph_name = 'six_vertex_network';

INSERT INTO classical_benchmarks (
    graph_id,
    algorithm_name,
    optimum_value,
    optimal_partition,
    execution_time_ms,
    verified
)
SELECT
    graph_id,
    'EXHAUSTIVE_SEARCH',
    8.0,
    '010101',
    1.5,
    TRUE
FROM optimization_graphs
WHERE graph_name = 'six_vertex_network';

-- ------------------------------------------------------------
-- 17. Execute the valid experiment
-- ------------------------------------------------------------

DO $$
DECLARE
    target_experiment BIGINT;
    target_graph BIGINT;
BEGIN
    SELECT experiment_id
    INTO target_experiment
    FROM experiments
    WHERE experiment_name = 'maxcut_qaoa_grid_search';

    SELECT graph_id
    INTO target_graph
    FROM optimization_graphs
    WHERE graph_name = 'six_vertex_network';

    CALL start_experiment(target_experiment);

    -- Demonstration parameter evaluations.
    -- A production quantum execution service writes these records
    -- after calculating the corresponding circuit expectation.

    INSERT INTO parameter_evaluations (
        experiment_id,
        evaluation_number,
        layer_number,
        gamma,
        beta,
        expected_cut,
        state_norm
    )
    VALUES
        (
            target_experiment,
            1,
            1,
            0.785398,
            0.392699,
            6.75,
            1.0
        ),
        (
            target_experiment,
            2,
            1,
            1.047198,
            0.523599,
            7.10,
            1.0
        ),
        (
            target_experiment,
            3,
            1,
            1.570796,
            0.785398,
            7.35,
            1.0
        ),
        (
            target_experiment,
            4,
            1,
            2.094395,
            1.047198,
            6.95,
            1.0
        );

    -- The sample measurements are validated against actual graph cuts.
    -- 010101 cuts all nine edges in this sample graph.

    INSERT INTO measurement_outcomes (
        experiment_id,
        bitstring,
        observed_cut,
        occurrence_count,
        probability
    )
    VALUES
        (
            target_experiment,
            '010101',
            9.0,
            55,
            0.55
        ),
        (
            target_experiment,
            '001101',
            6.0,
            30,
            0.30
        ),
        (
            target_experiment,
            '000000',
            0.0,
            15,
            0.15
        );

    CALL complete_experiment(target_experiment);
END;
$$;

-- ------------------------------------------------------------
-- 18. Retrieval: graph structure
-- ------------------------------------------------------------

SELECT
    g.graph_name,
    g.vertex_count,
    ge.source_vertex,
    ge.target_vertex,
    ge.weight
FROM optimization_graphs g
JOIN graph_edges ge
    ON ge.graph_id = g.graph_id
WHERE g.graph_name = 'six_vertex_network'
ORDER BY ge.source_vertex, ge.target_vertex;

-- ------------------------------------------------------------
-- 19. Eligibility evaluation
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    eligibility.eligible,
    eligibility.explanation
FROM experiments e
CROSS JOIN LATERAL
    check_experiment_eligibility(e.experiment_id) eligibility
ORDER BY e.experiment_id;

-- ------------------------------------------------------------
-- 20. Best parameter evaluation
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    bp.gamma,
    bp.beta,
    bp.expected_cut,
    bp.evaluation_number
FROM experiments e
JOIN experiment_best_parameters bp
    ON bp.experiment_id = e.experiment_id
ORDER BY bp.expected_cut DESC;

-- ------------------------------------------------------------
-- 21. Approximation ratio reporting
-- ------------------------------------------------------------

SELECT
    experiment_name,
    status,
    graph_name,
    vertex_count,
    edge_count,
    qaoa_depth,
    gamma,
    beta,
    expected_cut,
    classical_optimum,
    round(approximation_ratio::NUMERIC, 4)
        AS approximation_ratio
FROM experiment_performance_report
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- 22. Measurement aggregation
-- ------------------------------------------------------------

SELECT
    experiment_id,
    count(*) AS unique_outcomes,
    sum(occurrence_count) AS total_shots,
    sum(probability) AS recorded_probability_mass,
    max(observed_cut) AS highest_observed_cut,
    sum(observed_cut * occurrence_count)
        / NULLIF(sum(occurrence_count), 0)
        AS empirical_mean_cut
FROM measurement_outcomes
GROUP BY experiment_id
ORDER BY experiment_id;

-- ------------------------------------------------------------
-- 23. Workflow and audit history
-- ------------------------------------------------------------

SELECT
    e.experiment_name,
    a.previous_status,
    a.new_status,
    a.changed_at,
    a.reason
FROM experiment_audit a
JOIN experiments e
    ON e.experiment_id = a.experiment_id
ORDER BY a.changed_at;

COMMIT;

-- ------------------------------------------------------------
-- 24. Operational transaction example
-- ------------------------------------------------------------

-- To test transactional rollback, execute separately:
--
-- BEGIN;
-- UPDATE experiments
-- SET status = 'RUNNING'
-- WHERE experiment_name = 'maxcut_qaoa_grid_search';
-- ROLLBACK;
--
-- Invalid transitions are rejected by the status trigger.
