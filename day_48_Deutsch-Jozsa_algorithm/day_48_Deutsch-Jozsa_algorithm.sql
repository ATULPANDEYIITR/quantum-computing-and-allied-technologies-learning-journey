-- Deutsch-Jozsa Algorithm: PostgreSQL experiment registry and results.
--
-- PostgreSQL stores the classical oracle specification, truth table,
-- promise validation, and results of ideal or simulated quantum runs.
-- SQL does not execute quantum gates; it records and checks the evidence
-- supplied by a circuit implementation.

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TABLE IF NOT EXISTS oracle_experiment (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    oracle_name TEXT NOT NULL UNIQUE,
    input_width INTEGER NOT NULL CHECK (input_width BETWEEN 1 AND 20),
    expected_class TEXT NOT NULL
        CHECK (expected_class IN ('constant', 'balanced')),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oracle_truth_table (
    experiment_id BIGINT NOT NULL
        REFERENCES oracle_experiment(experiment_id) ON DELETE CASCADE,
    input_value INTEGER NOT NULL CHECK (input_value >= 0),
    output_value SMALLINT NOT NULL CHECK (output_value IN (0, 1)),
    PRIMARY KEY (experiment_id, input_value)
);

CREATE TABLE IF NOT EXISTS circuit_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES oracle_experiment(experiment_id) ON DELETE CASCADE,
    simulator_name TEXT NOT NULL,
    oracle_queries INTEGER NOT NULL CHECK (oracle_queries >= 0),
    zero_state_probability DOUBLE PRECISION NOT NULL
        CHECK (
            zero_state_probability >= 0.0
            AND zero_state_probability <= 1.0
        ),
    measured_bitstring TEXT NOT NULL,
    inferred_class TEXT NOT NULL
        CHECK (inferred_class IN ('constant', 'balanced')),
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_truth_table_output
    ON oracle_truth_table(experiment_id, output_value);

CREATE INDEX IF NOT EXISTS idx_circuit_run_experiment_time
    ON circuit_run(experiment_id, executed_at DESC);

-- A constant oracle returns the same value for every possible input.
-- A balanced oracle returns one for exactly half the input space.
INSERT INTO oracle_experiment
    (oracle_name, input_width, expected_class, description)
VALUES
    (
        'constant-zero-2',
        2,
        'constant',
        'Two-qubit oracle returning zero for every input'
    ),
    (
        'parity-2',
        2,
        'balanced',
        'Two-qubit oracle returning the parity of the input bits'
    )
ON CONFLICT (oracle_name) DO NOTHING;

-- Generate the complete truth tables for the example experiments.
INSERT INTO oracle_truth_table (experiment_id, input_value, output_value)
SELECT e.experiment_id, inputs.x,
       CASE
           WHEN e.oracle_name = 'constant-zero-2' THEN 0
           WHEN e.oracle_name = 'parity-2' THEN
               ((inputs.x >> 0) & 1) # ((inputs.x >> 1) & 1)
       END
FROM oracle_experiment AS e
CROSS JOIN generate_series(0, 3) AS inputs(x)
WHERE e.oracle_name IN ('constant-zero-2', 'parity-2')
ON CONFLICT (experiment_id, input_value) DO NOTHING;

-- Verify that every registered oracle has exactly 2^n truth-table rows,
-- and that the declared class agrees with the number of ones.
CREATE OR REPLACE VIEW oracle_validation AS
SELECT
    e.experiment_id,
    e.oracle_name,
    e.input_width,
    e.expected_class,
    COUNT(t.input_value) AS recorded_inputs,
    COUNT(t.input_value) FILTER (WHERE t.output_value = 1) AS one_count,
    (1::BIGINT << e.input_width) AS required_inputs,
    CASE
        WHEN COUNT(t.input_value) <> (1::BIGINT << e.input_width)
            THEN 'incomplete'
        WHEN COUNT(t.input_value) FILTER (WHERE t.output_value = 1) = 0
          OR COUNT(t.input_value) FILTER (WHERE t.output_value = 1)
             = (1::BIGINT << e.input_width)
            THEN
                CASE
                    WHEN e.expected_class = 'constant' THEN 'valid'
                    ELSE 'class_mismatch'
                END
        WHEN COUNT(t.input_value) FILTER (WHERE t.output_value = 1)
             * 2 = (1::BIGINT << e.input_width)
            THEN
                CASE
                    WHEN e.expected_class = 'balanced' THEN 'valid'
                    ELSE 'class_mismatch'
                END
        ELSE 'promise_violation'
    END AS validation_status
FROM oracle_experiment AS e
LEFT JOIN oracle_truth_table AS t
    ON t.experiment_id = e.experiment_id
GROUP BY e.experiment_id, e.oracle_name, e.input_width, e.expected_class;

-- Store ideal circuit outcomes: one oracle query, with the zero state
-- distinguishing constant and balanced functions.
INSERT INTO circuit_run (
    experiment_id,
    simulator_name,
    oracle_queries,
    zero_state_probability,
    measured_bitstring,
    inferred_class
)
SELECT
    experiment_id,
    'ideal-reference-model',
    1,
    CASE WHEN expected_class = 'constant' THEN 1.0 ELSE 0.0 END,
    CASE WHEN expected_class = 'constant' THEN '00' ELSE '01' END,
    expected_class
FROM oracle_validation
WHERE validation_status = 'valid'
ON CONFLICT DO NOTHING;

-- Evaluate whether recorded runs agree with the registered promise.
CREATE OR REPLACE VIEW experiment_audit AS
SELECT
    e.oracle_name,
    v.validation_status,
    r.run_id,
    r.simulator_name,
    r.oracle_queries,
    r.zero_state_probability,
    r.measured_bitstring,
    r.inferred_class,
    CASE
        WHEN v.validation_status <> 'valid' THEN 'oracle_invalid'
        WHEN r.run_id IS NULL THEN 'no_run'
        WHEN r.inferred_class <> e.expected_class THEN 'classification_mismatch'
        WHEN e.expected_class = 'constant'
             AND ABS(r.zero_state_probability - 1.0) > 1e-9
            THEN 'constant_probability_mismatch'
        WHEN e.expected_class = 'balanced'
             AND ABS(r.zero_state_probability) > 1e-9
            THEN 'balanced_probability_mismatch'
        WHEN r.oracle_queries <> 1 THEN 'query_count_mismatch'
        ELSE 'valid'
    END AS audit_status
FROM oracle_experiment AS e
JOIN oracle_validation AS v USING (experiment_id)
LEFT JOIN circuit_run AS r USING (experiment_id);

-- Inspection queries.
SELECT * FROM oracle_validation ORDER BY oracle_name;
SELECT * FROM experiment_audit ORDER BY oracle_name, run_id;

-- The truth-table key prevents duplicate inputs. The width constraint
-- and completeness view detect missing or invalid oracle specifications.
-- Roll back or commit according to the experiment-registry workflow.
COMMIT;
