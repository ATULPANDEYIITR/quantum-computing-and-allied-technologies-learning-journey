-- PostgreSQL 14+
-- Parameterized quantum circuits, symbolic variables, rotations, and evaluation runs.
-- The schema separates reusable circuit definitions from concrete parameter bindings.

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_lab;
SET search_path TO quantum_lab, public;

CREATE TYPE gate_kind AS ENUM ('H', 'RX', 'RY', 'RZ', 'CNOT');
CREATE TYPE parameter_role AS ENUM ('FEATURE', 'TRAINABLE', 'CALIBRATION');
CREATE TYPE evaluation_status AS ENUM ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED');

CREATE TABLE circuit (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name TEXT NOT NULL UNIQUE,
    qubit_count INTEGER NOT NULL CHECK (qubit_count BETWEEN 1 AND 16),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE circuit_parameter (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuit(circuit_id) ON DELETE CASCADE,
    parameter_name TEXT NOT NULL,
    role parameter_role NOT NULL,
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION,
    UNIQUE (circuit_id, parameter_name),
    CHECK (
        lower_bound IS NULL OR upper_bound IS NULL OR lower_bound <= upper_bound
    ),
    CHECK (lower_bound IS NULL OR lower_bound > '-Infinity'::DOUBLE PRECISION),
    CHECK (upper_bound IS NULL OR upper_bound < 'Infinity'::DOUBLE PRECISION)
);

CREATE TABLE circuit_gate (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuit(circuit_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    kind gate_kind NOT NULL,
    target_qubit INTEGER NOT NULL CHECK (target_qubit >= 0),
    control_qubit INTEGER,
    angle_constant DOUBLE PRECISION,
    angle_expression TEXT,
    UNIQUE (circuit_id, sequence_number),
    CHECK (
        (kind = 'CNOT' AND control_qubit IS NOT NULL
            AND control_qubit <> target_qubit
            AND angle_constant IS NULL AND angle_expression IS NULL)
        OR
        (kind IN ('RX', 'RY', 'RZ')
            AND control_qubit IS NULL
            AND ((angle_constant IS NOT NULL AND angle_expression IS NULL)
                OR (angle_constant IS NULL AND angle_expression IS NOT NULL)))
        OR
        (kind = 'H' AND control_qubit IS NULL
            AND angle_constant IS NULL AND angle_expression IS NULL)
    ),
    CHECK (
        angle_constant IS NULL
        OR angle_constant NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE TABLE circuit_evaluation (
    evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES circuit(circuit_id),
    evaluation_label TEXT NOT NULL,
    status evaluation_status NOT NULL DEFAULT 'QUEUED',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    UNIQUE (circuit_id, evaluation_label),
    CHECK (
        (status = 'FAILED' AND error_message IS NOT NULL)
        OR status <> 'FAILED'
    ),
    CHECK (
        completed_at IS NULL OR started_at IS NOT NULL
    ),
    CHECK (
        completed_at IS NULL OR completed_at >= started_at
    )
);

CREATE TABLE parameter_binding (
    evaluation_id BIGINT NOT NULL
        REFERENCES circuit_evaluation(evaluation_id) ON DELETE CASCADE,
    parameter_id BIGINT NOT NULL
        REFERENCES circuit_parameter(parameter_id) ON DELETE CASCADE,
    numeric_value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (evaluation_id, parameter_id),
    CHECK (
        numeric_value NOT IN (
            'Infinity'::DOUBLE PRECISION,
            '-Infinity'::DOUBLE PRECISION,
            'NaN'::DOUBLE PRECISION
        )
    )
);

CREATE TABLE evaluation_result (
    evaluation_id BIGINT NOT NULL
        REFERENCES circuit_evaluation(evaluation_id) ON DELETE CASCADE,
    basis_state TEXT NOT NULL,
    probability DOUBLE PRECISION NOT NULL CHECK (
        probability >= 0.0 AND probability <= 1.0
    ),
    PRIMARY KEY (evaluation_id, basis_state)
);

CREATE INDEX circuit_gate_execution_order
    ON circuit_gate(circuit_id, sequence_number);

CREATE INDEX evaluation_status_queue
    ON circuit_evaluation(requested_at)
    WHERE status = 'QUEUED';

CREATE INDEX parameter_binding_parameter_value
    ON parameter_binding(parameter_id, numeric_value);

CREATE VIEW circuit_parameter_inventory AS
SELECT
    c.circuit_name,
    c.qubit_count,
    p.parameter_name,
    p.role,
    p.lower_bound,
    p.upper_bound
FROM circuit AS c
JOIN circuit_parameter AS p USING (circuit_id);

CREATE VIEW evaluation_binding_completeness AS
SELECT
    e.evaluation_id,
    e.evaluation_label,
    c.circuit_name,
    COUNT(p.parameter_id) AS expected_parameters,
    COUNT(b.parameter_id) AS bound_parameters,
    COUNT(p.parameter_id) = COUNT(b.parameter_id) AS all_parameters_bound
FROM circuit_evaluation AS e
JOIN circuit AS c USING (circuit_id)
LEFT JOIN circuit_parameter AS p USING (circuit_id)
LEFT JOIN parameter_binding AS b
    ON b.evaluation_id = e.evaluation_id
   AND b.parameter_id = p.parameter_id
GROUP BY e.evaluation_id, e.evaluation_label, c.circuit_name;

-- Database validation prevents gate targets and CNOT controls from exceeding
-- the circuit width. A trigger is required because the rule spans tables.
CREATE FUNCTION validate_gate_qubits()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    width INTEGER;
BEGIN
    SELECT qubit_count INTO width
    FROM circuit
    WHERE circuit_id = NEW.circuit_id;

    IF NEW.target_qubit >= width THEN
        RAISE EXCEPTION 'Target qubit % exceeds circuit width %',
            NEW.target_qubit, width;
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND (NEW.control_qubit < 0 OR NEW.control_qubit >= width) THEN
        RAISE EXCEPTION 'Control qubit % exceeds circuit width %',
            NEW.control_qubit, width;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER circuit_gate_qubit_guard
BEFORE INSERT OR UPDATE ON circuit_gate
FOR EACH ROW EXECUTE FUNCTION validate_gate_qubits();

CREATE FUNCTION validate_parameter_binding()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_circuit BIGINT;
    actual_circuit BIGINT;
    low_value DOUBLE PRECISION;
    high_value DOUBLE PRECISION;
BEGIN
    SELECT circuit_id, lower_bound, upper_bound
    INTO expected_circuit, low_value, high_value
    FROM circuit_parameter
    WHERE parameter_id = NEW.parameter_id;

    SELECT circuit_id INTO actual_circuit
    FROM circuit_evaluation
    WHERE evaluation_id = NEW.evaluation_id;

    IF expected_circuit <> actual_circuit THEN
        RAISE EXCEPTION
            'Parameter and evaluation belong to different circuits';
    END IF;

    IF low_value IS NOT NULL AND NEW.numeric_value < low_value THEN
        RAISE EXCEPTION 'Parameter value is below its configured bound';
    END IF;

    IF high_value IS NOT NULL AND NEW.numeric_value > high_value THEN
        RAISE EXCEPTION 'Parameter value exceeds its configured bound';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER parameter_binding_guard
BEFORE INSERT OR UPDATE ON parameter_binding
FOR EACH ROW EXECUTE FUNCTION validate_parameter_binding();

CREATE FUNCTION check_evaluation_ready(p_evaluation_id BIGINT)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
AS $$
    SELECT
        e.status = 'QUEUED'
        AND NOT EXISTS (
            SELECT 1
            FROM circuit_parameter AS p
            WHERE p.circuit_id = e.circuit_id
              AND NOT EXISTS (
                  SELECT 1
                  FROM parameter_binding AS b
                  WHERE b.evaluation_id = e.evaluation_id
                    AND b.parameter_id = p.parameter_id
              )
        )
    FROM circuit_evaluation AS e
    WHERE e.evaluation_id = p_evaluation_id
$$;

INSERT INTO circuit (circuit_name, qubit_count, description)
VALUES (
    'sensor_calibration',
    2,
    'Two-qubit circuit with input phase, trainable drive, and calibration offset.'
);

INSERT INTO circuit_parameter
    (circuit_id, parameter_name, role, lower_bound, upper_bound)
SELECT circuit_id, 'phase', 'FEATURE', -6.283185307, 6.283185307
FROM circuit WHERE circuit_name = 'sensor_calibration'
UNION ALL
SELECT circuit_id, 'drive', 'TRAINABLE', -3.141592654, 3.141592654
FROM circuit WHERE circuit_name = 'sensor_calibration'
UNION ALL
SELECT circuit_id, 'offset', 'CALIBRATION', -3.141592654, 3.141592654
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit)
SELECT circuit_id, 0, 'H', 0
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit, angle_expression)
SELECT circuit_id, 1, 'RY', 0, 'phase'
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit, angle_expression)
SELECT circuit_id, 2, 'RX', 1, 'drive'
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit, control_qubit)
SELECT circuit_id, 3, 'CNOT', 1, 0
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit, angle_expression)
SELECT circuit_id, 4, 'RZ', 0, 'offset + drive * 0.5'
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_gate
    (circuit_id, sequence_number, kind, target_qubit, angle_expression)
SELECT circuit_id, 5, 'RY', 1, 'phase * 2'
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO circuit_evaluation (circuit_id, evaluation_label)
SELECT circuit_id, 'baseline-calibration'
FROM circuit WHERE circuit_name = 'sensor_calibration';

INSERT INTO parameter_binding (evaluation_id, parameter_id, numeric_value)
SELECT e.evaluation_id, p.parameter_id,
       CASE p.parameter_name
           WHEN 'phase' THEN 0.65
           WHEN 'drive' THEN -0.35
           WHEN 'offset' THEN 0.12
       END
FROM circuit_evaluation AS e
JOIN circuit AS c USING (circuit_id)
JOIN circuit_parameter AS p USING (circuit_id)
WHERE c.circuit_name = 'sensor_calibration'
  AND e.evaluation_label = 'baseline-calibration';

-- The SQL model stores symbolic expressions but does not parse or execute them.
-- A quantum runtime must evaluate the expressions and produce measured results.
SELECT
    c.circuit_name,
    g.sequence_number,
    g.kind,
    g.target_qubit,
    g.control_qubit,
    g.angle_constant,
    g.angle_expression
FROM circuit AS c
JOIN circuit_gate AS g USING (circuit_id)
WHERE c.circuit_name = 'sensor_calibration'
ORDER BY g.sequence_number;

SELECT *
FROM evaluation_binding_completeness
ORDER BY evaluation_id;

SELECT check_evaluation_ready(
    (SELECT evaluation_id
     FROM circuit_evaluation
     WHERE evaluation_label = 'baseline-calibration')
) AS ready_for_execution;

-- Demonstrate a rejected cross-circuit binding and out-of-range gate.
-- Each exception is caught in a PL/pgSQL block so the full script remains runnable.
DO $$
DECLARE
    evaluation_id_value BIGINT;
    parameter_id_value BIGINT;
BEGIN
    SELECT evaluation_id INTO evaluation_id_value
    FROM circuit_evaluation
    WHERE evaluation_label = 'baseline-calibration';

    INSERT INTO circuit (circuit_name, qubit_count, description)
    VALUES ('independent_test', 1, 'Separate circuit for integrity tests.');

    INSERT INTO circuit_parameter (circuit_id, parameter_name, role)
    SELECT circuit_id, 'other_angle', 'TRAINABLE'
    FROM circuit WHERE circuit_name = 'independent_test'
    RETURNING parameter_id INTO parameter_id_value;

    BEGIN
        INSERT INTO parameter_binding
            (evaluation_id, parameter_id, numeric_value)
        VALUES (evaluation_id_value, parameter_id_value, 0.5);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Rejected cross-circuit binding: %', SQLERRM;
    END;

    BEGIN
        INSERT INTO circuit_gate
            (circuit_id, sequence_number, kind, target_qubit, angle_expression)
        SELECT circuit_id, 0, 'RY', 4, 'other_angle'
        FROM circuit WHERE circuit_name = 'independent_test';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Rejected out-of-range gate: %', SQLERRM;
    END;
END;
$$;

-- Result rows are committed only after the producing runtime supplies a valid
-- normalized distribution. The database enforces per-row bounds; a deferred
-- aggregate check or application transaction should enforce total probability.
INSERT INTO evaluation_result (evaluation_id, basis_state, probability)
SELECT e.evaluation_id, sample.basis_state, sample.probability
FROM circuit_evaluation AS e
JOIN circuit AS c USING (circuit_id)
CROSS JOIN (
    VALUES
        ('00', 0.40::DOUBLE PRECISION),
        ('01', 0.10::DOUBLE PRECISION),
        ('10', 0.20::DOUBLE PRECISION),
        ('11', 0.30::DOUBLE PRECISION)
) AS sample(basis_state, probability)
WHERE c.circuit_name = 'sensor_calibration'
  AND e.evaluation_label = 'baseline-calibration';

SELECT
    e.evaluation_label,
    SUM(r.probability) AS total_probability,
    ABS(SUM(r.probability) - 1.0) < 1e-9 AS normalized
FROM circuit_evaluation AS e
JOIN evaluation_result AS r USING (evaluation_id)
GROUP BY e.evaluation_id, e.evaluation_label;

COMMIT;
