DROP SCHEMA IF EXISTS quantum_walks CASCADE;
CREATE SCHEMA quantum_walks;

SET search_path TO quantum_walks, public;

CREATE TYPE walk_model AS ENUM (
    'discrete_coined',
    'continuous_time'
);

CREATE TYPE application_type AS ENUM (
    'search',
    'network_routing',
    'quantum_simulation',
    'graph_analysis'
);

CREATE TYPE experiment_status AS ENUM (
    'planned',
    'running',
    'completed',
    'failed'
);

CREATE TABLE graph (
    graph_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_name TEXT NOT NULL UNIQUE,
    vertex_count INTEGER NOT NULL CHECK (vertex_count > 0),
    directed BOOLEAN NOT NULL DEFAULT FALSE,
    weighted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vertex (
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id) ON DELETE CASCADE,
    vertex_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (graph_id, vertex_id),
    UNIQUE (graph_id, label),
    CHECK (vertex_id >= 0)
);

CREATE TABLE graph_edge (
    graph_id BIGINT NOT NULL,
    source_vertex INTEGER NOT NULL,
    target_vertex INTEGER NOT NULL,
    weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    PRIMARY KEY (graph_id, source_vertex, target_vertex),
    FOREIGN KEY (graph_id, source_vertex)
        REFERENCES vertex(graph_id, vertex_id)
        ON DELETE CASCADE,
    FOREIGN KEY (graph_id, target_vertex)
        REFERENCES vertex(graph_id, vertex_id)
        ON DELETE CASCADE,
    CHECK (source_vertex <> target_vertex),
    CHECK (weight > 0)
);

CREATE TABLE quantum_experiment (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id BIGINT NOT NULL REFERENCES graph(graph_id),
    model walk_model NOT NULL,
    application application_type NOT NULL,
    start_vertex INTEGER NOT NULL,
    target_vertex INTEGER,
    evolution_time DOUBLE PRECISION NOT NULL DEFAULT 0,
    steps INTEGER NOT NULL DEFAULT 0,
    status experiment_status NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    FOREIGN KEY (graph_id, start_vertex)
        REFERENCES vertex(graph_id, vertex_id),
    FOREIGN KEY (graph_id, target_vertex)
        REFERENCES vertex(graph_id, vertex_id),
    CHECK (evolution_time >= 0),
    CHECK (steps >= 0),
    CHECK (
        (model = 'continuous_time' AND evolution_time >= 0)
        OR
        (model = 'discrete_coined')
    )
);

CREATE TABLE probability_observation (
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiment(experiment_id)
        ON DELETE CASCADE,
    vertex_id INTEGER NOT NULL,
    probability DOUBLE PRECISION NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (experiment_id, vertex_id),
    FOREIGN KEY (
        (SELECT graph_id FROM quantum_experiment
         WHERE quantum_experiment.experiment_id = probability_observation.experiment_id),
        vertex_id
    ) REFERENCES vertex(graph_id, vertex_id)
);

CREATE TABLE application_requirement (
    application application_type PRIMARY KEY,
    minimum_probability DOUBLE PRECISION NOT NULL,
    description TEXT NOT NULL,
    CHECK (
        minimum_probability >= 0
        AND minimum_probability <= 1
    )
);

CREATE TABLE experiment_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES quantum_experiment(experiment_id)
        ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_message TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_graph_edge_source
    ON graph_edge(graph_id, source_vertex);

CREATE INDEX idx_experiment_status
    ON quantum_experiment(status);

CREATE INDEX idx_observation_probability
    ON probability_observation(experiment_id, probability DESC);

CREATE INDEX idx_event_experiment_time
    ON experiment_event(experiment_id, event_time DESC);

INSERT INTO graph (
    graph_name,
    vertex_count,
    directed,
    weighted
)
VALUES
    ('four_cycle', 4, FALSE, FALSE),
    ('network_search', 6, FALSE, FALSE);

INSERT INTO vertex (graph_id, vertex_id, label)
SELECT graph_id, v, 'v' || v
FROM graph
CROSS JOIN generate_series(0, vertex_count - 1) AS v;

INSERT INTO graph_edge (
    graph_id,
    source_vertex,
    target_vertex
)
SELECT g.graph_id, e.source_vertex, e.target_vertex
FROM graph g
CROSS JOIN (
    VALUES
        (0, 1), (1, 0),
        (1, 2), (2, 1),
        (2, 3), (3, 2),
        (3, 0), (0, 3)
) AS e(source_vertex, target_vertex)
WHERE g.graph_name = 'four_cycle';

INSERT INTO graph_edge (
    graph_id,
    source_vertex,
    target_vertex
)
SELECT g.graph_id, e.source_vertex, e.target_vertex
FROM graph g
CROSS JOIN (
    VALUES
        (0, 1), (1, 0),
        (0, 2), (2, 0),
        (1, 3), (3, 1),
        (2, 4), (4, 2),
        (3, 5), (5, 3),
        (4, 5), (5, 4)
) AS e(source_vertex, target_vertex)
WHERE g.graph_name = 'network_search';

INSERT INTO application_requirement (
    application,
    minimum_probability,
    description
)
VALUES
    ('search', 0.20, 'Candidate target probability for graph search.'),
    ('network_routing', 0.10, 'Minimum probability used for route ranking.'),
    ('quantum_simulation', 0.01, 'Minimum observable probability.'),
    ('graph_analysis', 0.05, 'Threshold for graph-analysis experiments.');

CREATE OR REPLACE FUNCTION validate_experiment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    graph_vertices INTEGER;
BEGIN
    SELECT vertex_count
    INTO graph_vertices
    FROM graph
    WHERE graph_id = NEW.graph_id;

    IF graph_vertices IS NULL THEN
        RAISE EXCEPTION 'Graph % does not exist.', NEW.graph_id;
    END IF;

    IF NEW.start_vertex >= graph_vertices THEN
        RAISE EXCEPTION
            'Start vertex % is outside graph size %.',
            NEW.start_vertex,
            graph_vertices;
    END IF;

    IF NEW.target_vertex IS NOT NULL
       AND NEW.target_vertex >= graph_vertices THEN
        RAISE EXCEPTION
            'Target vertex % is outside graph size %.',
            NEW.target_vertex,
            graph_vertices;
    END IF;

    IF NEW.model = 'discrete_coined' AND NEW.steps = 0 THEN
        IF NEW.evolution_time <> 0 THEN
            RAISE EXCEPTION
                'Discrete coined walks use steps rather than evolution_time.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_experiment
BEFORE INSERT OR UPDATE
ON quantum_experiment
FOR EACH ROW
EXECUTE FUNCTION validate_experiment();

CREATE OR REPLACE FUNCTION validate_probability()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.probability < 0 OR NEW.probability > 1 THEN
        RAISE EXCEPTION
            'Probability must be between 0 and 1: %',
            NEW.probability;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_probability
BEFORE INSERT OR UPDATE
ON probability_observation
FOR EACH ROW
EXECUTE FUNCTION validate_probability();

CREATE OR REPLACE FUNCTION probability_total(
    p_experiment_id BIGINT
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(SUM(probability), 0.0)
    FROM probability_observation
    WHERE experiment_id = p_experiment_id;
$$;

CREATE OR REPLACE FUNCTION target_probability(
    p_experiment_id BIGINT
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(
        (
            SELECT po.probability
            FROM probability_observation po
            JOIN quantum_experiment qe
              ON qe.experiment_id = po.experiment_id
            WHERE po.experiment_id = p_experiment_id
              AND po.vertex_id = qe.target_vertex
        ),
        0.0
    );
$$;

CREATE OR REPLACE VIEW experiment_report AS
SELECT
    qe.experiment_id,
    g.graph_name,
    qe.model,
    qe.application,
    qe.start_vertex,
    qe.target_vertex,
    qe.evolution_time,
    qe.steps,
    qe.status,
    ROUND(probability_total(qe.experiment_id)::numeric, 8)
        AS total_probability,
    ROUND(target_probability(qe.experiment_id)::numeric, 8)
        AS target_probability,
    qe.created_at,
    qe.completed_at
FROM quantum_experiment qe
JOIN graph g
  ON g.graph_id = qe.graph_id;

CREATE OR REPLACE VIEW eligible_targets AS
SELECT
    qe.experiment_id,
    g.graph_name,
    qe.application,
    po.vertex_id AS target_vertex,
    po.probability,
    ar.minimum_probability,
    po.probability >= ar.minimum_probability AS eligible
FROM quantum_experiment qe
JOIN graph g
  ON g.graph_id = qe.graph_id
JOIN probability_observation po
  ON po.experiment_id = qe.experiment_id
JOIN application_requirement ar
  ON ar.application = qe.application
WHERE po.probability >= ar.minimum_probability;

BEGIN;

INSERT INTO quantum_experiment (
    graph_id,
    model,
    application,
    start_vertex,
    target_vertex,
    evolution_time,
    steps,
    status
)
SELECT
    graph_id,
    'continuous_time',
    'search',
    0,
    2,
    1.5,
    0,
    'completed'
FROM graph
WHERE graph_name = 'four_cycle';

INSERT INTO probability_observation (
    experiment_id,
    vertex_id,
    probability
)
SELECT
    currval('quantum_experiments_experiment_id_seq'),
    vertex_id,
    probability
FROM (
    VALUES
        (0, 0.25),
        (1, 0.25),
        (2, 0.25),
        (3, 0.25)
) AS observations(vertex_id, probability);

INSERT INTO experiment_event (
    experiment_id,
    event_type,
    event_message
)
VALUES (
    currval('quantum_experiments_experiment_id_seq'),
    'completed',
    'Continuous-time quantum-walk experiment completed.'
);

COMMIT;

-- The report distinguishes the walk model from its application and
-- exposes the target probability separately from the total normalization.
SELECT *
FROM experiment_report
ORDER BY experiment_id;

-- CTE-based normalization validation.
WITH totals AS (
    SELECT
        experiment_id,
        SUM(probability) AS probability_sum
    FROM probability_observation
    GROUP BY experiment_id
)
SELECT
    experiment_id,
    probability_sum,
    ABS(probability_sum - 1.0) AS normalization_error,
    CASE
        WHEN ABS(probability_sum - 1.0) < 0.000001
        THEN 'valid'
        ELSE 'invalid'
    END AS validation_status
FROM totals
ORDER BY experiment_id;

-- Target eligibility is based on the application-specific threshold.
SELECT
    experiment_id,
    graph_name,
    application,
    target_vertex,
    ROUND(probability::numeric, 6) AS probability,
    minimum_probability,
    eligible
FROM eligible_targets
ORDER BY experiment_id, probability DESC;

-- Rank candidate vertices by observed probability.
WITH ranked AS (
    SELECT
        qe.experiment_id,
        po.vertex_id,
        po.probability,
        RANK() OVER (
            PARTITION BY qe.experiment_id
            ORDER BY po.probability DESC
        ) AS probability_rank
    FROM quantum_experiment qe
    JOIN probability_observation po
      ON po.experiment_id = qe.experiment_id
)
SELECT *
FROM ranked
ORDER BY experiment_id, probability_rank, vertex_id;

-- Graph topology query used to identify the degree of each vertex.
SELECT
    g.graph_name,
    v.vertex_id,
    v.label,
    COUNT(ge.target_vertex) AS degree
FROM graph g
JOIN vertex v
  ON v.graph_id = g.graph_id
LEFT JOIN graph_edge ge
  ON ge.graph_id = v.graph_id
 AND ge.source_vertex = v.vertex_id
GROUP BY
    g.graph_name,
    v.vertex_id,
    v.label
ORDER BY
    g.graph_name,
    v.vertex_id;

-- Transactional failure example. The exception is caught so the script
-- remains executable while demonstrating database-level validation.
DO $$
BEGIN
    BEGIN
        INSERT INTO quantum_experiment (
            graph_id,
            model,
            application,
            start_vertex,
            target_vertex,
            evolution_time,
            steps,
            status
        )
        SELECT
            graph_id,
            'continuous_time',
            'search',
            99,
            1,
            2.0,
            0,
            'planned'
        FROM graph
        WHERE graph_name = 'four_cycle';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Expected validation failure: %', SQLERRM;
    END;
END;
$$;

-- Operational state aggregation.
SELECT
    status,
    COUNT(*) AS experiment_count
FROM quantum_experiment
GROUP BY status
ORDER BY status;
