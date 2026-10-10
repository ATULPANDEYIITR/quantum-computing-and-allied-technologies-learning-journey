-- PostgreSQL 15+ quantum circuit laboratory.
-- The schema stores circuits, ordered gate operations, simulation runs,
-- and measurement outcomes. It does not claim to execute quantum gates in SQL.

BEGIN;

DROP SCHEMA IF EXISTS quantum_lab CASCADE;
CREATE SCHEMA quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TYPE gate_kind AS ENUM (
    'I', 'X', 'Y', 'Z', 'H', 'S', 'T',
    'RX', 'RY', 'RZ', 'CNOT', 'CZ', 'SWAP'
);

CREATE TYPE run_status AS ENUM ('queued', 'running', 'completed', 'failed');

CREATE TABLE circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name TEXT NOT NULL,
    qubit_count INTEGER NOT NULL CHECK (qubit_count BETWEEN 1 AND 30),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (circuit_name, created_at)
);

CREATE TABLE gate_operations (
    operation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id) ON DELETE CASCADE,
    sequence_no INTEGER NOT NULL CHECK (sequence_no >= 0),
    gate gate_kind NOT NULL,
    target_qubit INTEGER NOT NULL CHECK (target_qubit >= 0),
    second_target INTEGER CHECK (second_target >= 0),
    control_qubit INTEGER CHECK (control_qubit >= 0),
    angle_radians DOUBLE PRECISION,
    UNIQUE (circuit_id, sequence_no),
    CHECK (
        (gate IN ('I', 'X', 'Y', 'Z', 'H', 'S', 'T')
            AND second_target IS NULL
            AND control_qubit IS NULL
            AND angle_radians IS NULL)
        OR
        (gate IN ('RX', 'RY', 'RZ')
            AND second_target IS NULL
            AND control_qubit IS NULL
            AND angle_radians IS NOT NULL
            AND angle_radians > '-Infinity'::DOUBLE PRECISION
            AND angle_radians < 'Infinity'::DOUBLE PRECISION)
        OR
        (gate IN ('CNOT', 'CZ')
            AND second_target IS NULL
            AND control_qubit IS NOT NULL
            AND angle_radians IS NULL
            AND control_qubit <> target_qubit)
        OR
        (gate = 'SWAP'
            AND second_target IS NOT NULL
            AND control_qubit IS NULL
            AND angle_radians IS NULL
            AND second_target <> target_qubit)
    )
);

CREATE TABLE simulation_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuits(circuit_id) ON DELETE RESTRICT,
    status run_status NOT NULL DEFAULT 'queued',
    shots INTEGER NOT NULL CHECK (shots BETWEEN 1 AND 10000000),
    simulator_name TEXT NOT NULL,
    simulator_version TEXT NOT NULL,
    seed BIGINT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        (status = 'queued' AND started_at IS NULL AND finished_at IS NULL)
        OR
        (status = 'running' AND started_at IS NOT NULL AND finished_at IS NULL)
        OR
        (status = 'completed' AND started_at IS NOT NULL
            AND finished_at IS NOT NULL AND error_message IS NULL)
        OR
        (status = 'failed' AND started_at IS NOT NULL
            AND finished_at IS NOT NULL AND error_message IS NOT NULL)
    )
);

CREATE TABLE measurement_results (
    run_id BIGINT NOT NULL REFERENCES simulation_runs(run_id) ON DELETE CASCADE,
    bitstring TEXT NOT NULL,
    observed_shots INTEGER NOT NULL CHECK (observed_shots >= 0),
    PRIMARY KEY (run_id, bitstring),
    CHECK (bitstring ~ '^[01]+$')
);

CREATE INDEX idx_operations_circuit_sequence
    ON gate_operations(circuit_id, sequence_no);

CREATE INDEX idx_runs_status_created
    ON simulation_runs(status, created_at DESC);

CREATE INDEX idx_results_bitstring
    ON measurement_results(bitstring);

-- Validate qubit indices and the gate's multi-qubit shape against its circuit.
CREATE FUNCTION validate_gate_operation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    total_qubits INTEGER;
BEGIN
    SELECT qubit_count INTO total_qubits
    FROM circuits
    WHERE circuit_id = NEW.circuit_id;

    IF total_qubits IS NULL THEN
        RAISE EXCEPTION 'Circuit % does not exist', NEW.circuit_id;
    END IF;

    IF NEW.target_qubit >= total_qubits
       OR (NEW.second_target IS NOT NULL AND NEW.second_target >= total_qubits)
       OR (NEW.control_qubit IS NOT NULL AND NEW.control_qubit >= total_qubits) THEN
        RAISE EXCEPTION 'Gate qubit index exceeds circuit size';
    END IF;

    IF NEW.gate IN ('CNOT', 'CZ') AND NEW.control_qubit IS NULL THEN
        RAISE EXCEPTION '% requires a control qubit', NEW.gate;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER gate_operation_validation
BEFORE INSERT OR UPDATE ON gate_operations
FOR EACH ROW EXECUTE FUNCTION validate_gate_operation();

-- State transitions are restricted so a completed run cannot silently be restarted.
CREATE FUNCTION validate_run_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status <> NEW.status THEN
        IF NOT (
            (OLD.status = 'queued' AND NEW.status IN ('running', 'failed'))
            OR (OLD.status = 'running' AND NEW.status IN ('completed', 'failed'))
        ) THEN
            RAISE EXCEPTION 'Invalid run transition: % -> %', OLD.status, NEW.status;
        END IF;
    END IF;

    IF NEW.status = 'running' AND NEW.started_at IS NULL THEN
        NEW.started_at := now();
    END IF;

    IF NEW.status IN ('completed', 'failed') AND NEW.finished_at IS NULL THEN
        NEW.finished_at := now();
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER run_transition_validation
BEFORE UPDATE ON simulation_runs
FOR EACH ROW EXECUTE FUNCTION validate_run_transition();

-- Each operation is validated before insertion, while circuit size is enforced
-- through the trigger because ordinary CHECK constraints cannot query another table.
INSERT INTO circuits (circuit_name, qubit_count, description)
VALUES
    ('bell_pair', 2, 'Hadamard followed by controlled-X'),
    ('rotation_demo', 1, 'Single-qubit Y-axis rotation'),
    ('interference_demo', 1, 'Hadamard, phase flip, Hadamard');

INSERT INTO gate_operations
    (circuit_id, sequence_no, gate, target_qubit, control_qubit, angle_radians)
VALUES
    (1, 0, 'H', 0, NULL, NULL);

INSERT INTO gate_operations
    (circuit_id, sequence_no, gate, target_qubit, control_qubit, angle_radians)
VALUES
    (1, 1, 'CNOT', 1, 0, NULL);

INSERT INTO gate_operations
    (circuit_id, sequence_no, gate, target_qubit, control_qubit, angle_radians)
VALUES
    (2, 0, 'RY', 0, NULL, pi() / 3);

INSERT INTO gate_operations
    (circuit_id, sequence_no, gate, target_qubit, control_qubit, angle_radians)
VALUES
    (3, 0, 'H', 0, NULL, NULL),
    (3, 1, 'Z', 0, NULL, NULL),
    (3, 2, 'H', 0, NULL, NULL);

INSERT INTO simulation_runs
    (circuit_id, shots, simulator_name, simulator_version, seed)
VALUES
    (1, 2000, 'state-vector-demo', '1.0', 1234),
    (2, 1000, 'state-vector-demo', '1.0', 5678),
    (3, 1000, 'state-vector-demo', '1.0', 9012);

UPDATE simulation_runs
SET status = 'running'
WHERE run_id IN (1, 2, 3);

-- These are illustrative simulator observations for relational workflow practice.
-- They are sample data, not the result of executing a quantum simulator in SQL.
INSERT INTO measurement_results (run_id, bitstring, observed_shots)
VALUES
    (1, '00', 1010),
    (1, '11', 990),
    (2, '0', 744),
    (2, '1', 256),
    (3, '0', 0),
    (3, '1', 1000);

UPDATE simulation_runs
SET status = 'completed'
WHERE run_id IN (1, 2, 3);

-- Inspect the executable circuit definition in operation order.
SELECT c.circuit_name, c.qubit_count, g.sequence_no, g.gate,
       g.target_qubit, g.control_qubit, g.second_target, g.angle_radians
FROM circuits AS c
JOIN gate_operations AS g USING (circuit_id)
ORDER BY c.circuit_id, g.sequence_no;

-- Compare observed frequencies with ideal circuit expectations.
-- The Bell circuit ideally has P(00) = P(11) = 0.5.
SELECT c.circuit_name,
       m.bitstring,
       m.observed_shots,
       r.shots,
       round(m.observed_shots::NUMERIC / r.shots, 4) AS observed_probability
FROM measurement_results AS m
JOIN simulation_runs AS r USING (run_id)
JOIN circuits AS c USING (circuit_id)
ORDER BY r.run_id, m.bitstring;

-- Check that each completed run accounts for all requested shots.
SELECT r.run_id, c.circuit_name, r.shots,
       COALESCE(SUM(m.observed_shots), 0) AS recorded_shots,
       COALESCE(SUM(m.observed_shots), 0) = r.shots AS shot_count_matches
FROM simulation_runs AS r
JOIN circuits AS c USING (circuit_id)
LEFT JOIN measurement_results AS m USING (run_id)
WHERE r.status = 'completed'
GROUP BY r.run_id, c.circuit_name, r.shots
ORDER BY r.run_id;

-- Identify malformed measurement lengths relative to circuit width.
SELECT r.run_id, c.circuit_name, c.qubit_count, m.bitstring
FROM measurement_results AS m
JOIN simulation_runs AS r USING (run_id)
JOIN circuits AS c USING (circuit_id)
WHERE length(m.bitstring) <> c.qubit_count;

-- Demonstrate rollback-safe failure handling without leaving invalid data.
SAVEPOINT invalid_gate_test;
DO $$
BEGIN
    BEGIN
        INSERT INTO gate_operations
            (circuit_id, sequence_no, gate, target_qubit)
        VALUES (2, 10, 'H', 5);
        RAISE EXCEPTION 'Expected invalid qubit index to be rejected';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Invalid gate rejected: %', SQLERRM;
    END;
END;
$$;
ROLLBACK TO SAVEPOINT invalid_gate_test;
RELEASE SAVEPOINT invalid_gate_test;

COMMIT;
