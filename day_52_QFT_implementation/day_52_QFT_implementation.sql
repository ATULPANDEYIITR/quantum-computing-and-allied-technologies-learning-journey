DROP SCHEMA IF EXISTS qft_lab CASCADE;
CREATE SCHEMA qft_lab;

SET search_path = qft_lab;

-- PostgreSQL represents the circuit as a relational workflow:
-- circuits -> qubits -> ordered gates -> execution records.
-- This keeps gate construction auditable and allows circuit validation
-- without storing a dense 2^n x 2^n Fourier matrix.

CREATE TYPE circuit_status AS ENUM (
    'DRAFT',
    'VALIDATED',
    'EXECUTED',
    'REJECTED'
);

CREATE TYPE gate_type AS ENUM (
    'HADAMARD',
    'CONTROLLED_PHASE',
    'SWAP'
);

CREATE TYPE execution_status AS ENUM (
    'ACCEPTED',
    'REJECTED',
    'COMPLETED'
);

CREATE TABLE circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name TEXT NOT NULL UNIQUE,
    qubit_count INTEGER NOT NULL
        CHECK (qubit_count BETWEEN 1 AND 20),
    status circuit_status NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMPTZ
);

CREATE TABLE circuit_gates (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    gate_position INTEGER NOT NULL
        CHECK (gate_position > 0),
    gate_type gate_type NOT NULL,
    target_qubit INTEGER NOT NULL
        CHECK (target_qubit >= 0),
    control_qubit INTEGER,
    second_qubit INTEGER,
    rotation_angle DOUBLE PRECISION,
    CONSTRAINT unique_gate_position
        UNIQUE (circuit_id, gate_position),
    CONSTRAINT controlled_phase_shape CHECK (
        (
            gate_type = 'CONTROLLED_PHASE'
            AND control_qubit IS NOT NULL
            AND rotation_angle IS NOT NULL
            AND control_qubit <> target_qubit
        )
        OR
        (
            gate_type <> 'CONTROLLED_PHASE'
            AND control_qubit IS NULL
            AND rotation_angle IS NULL
        )
    ),
    CONSTRAINT swap_shape CHECK (
        (
            gate_type = 'SWAP'
            AND second_qubit IS NOT NULL
            AND second_qubit <> target_qubit
        )
        OR
        (
            gate_type <> 'SWAP'
            AND second_qubit IS NULL
        )
    )
);

CREATE TABLE basis_states (
    state_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    basis_index BIGINT NOT NULL
        CHECK (basis_index >= 0),
    label TEXT NOT NULL,
    UNIQUE (circuit_id, basis_index)
);

CREATE TABLE executions (
    execution_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id),
    state_id BIGINT
        REFERENCES basis_states(state_id),
    direction TEXT NOT NULL
        CHECK (direction IN ('FORWARD', 'INVERSE')),
    status execution_status NOT NULL,
    normalization_error DOUBLE PRECISION NOT NULL
        CHECK (normalization_error >= 0),
    maximum_reference_error DOUBLE PRECISION,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    failure_reason TEXT
);

CREATE TABLE execution_gate_events (
    execution_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    execution_id BIGINT NOT NULL
        REFERENCES executions(execution_id)
        ON DELETE CASCADE,
    gate_id BIGINT NOT NULL
        REFERENCES circuit_gates(gate_id),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (execution_id, gate_id)
);

CREATE INDEX idx_circuit_gates_execution_order
    ON circuit_gates(circuit_id, gate_position);

CREATE INDEX idx_executions_circuit_status
    ON executions(circuit_id, status);

CREATE OR REPLACE FUNCTION validate_qft_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    circuit_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO circuit_qubits
    FROM circuits
    WHERE circuit_id = NEW.circuit_id;

    IF circuit_qubits IS NULL THEN
        RAISE EXCEPTION 'Circuit % does not exist', NEW.circuit_id;
    END IF;

    IF NEW.target_qubit >= circuit_qubits THEN
        RAISE EXCEPTION
            'Target qubit % exceeds circuit width %',
            NEW.target_qubit,
            circuit_qubits;
    END IF;

    IF NEW.control_qubit IS NOT NULL
       AND NEW.control_qubit >= circuit_qubits THEN
        RAISE EXCEPTION
            'Control qubit % exceeds circuit width %',
            NEW.control_qubit,
            circuit_qubits;
    END IF;

    IF NEW.second_qubit IS NOT NULL
       AND NEW.second_qubit >= circuit_qubits THEN
        RAISE EXCEPTION
            'Second qubit % exceeds circuit width %',
            NEW.second_qubit,
            circuit_qubits;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_qft_gate
BEFORE INSERT OR UPDATE ON circuit_gates
FOR EACH ROW
EXECUTE FUNCTION validate_qft_gate();

CREATE OR REPLACE FUNCTION qft_expected_gate_count(
    p_qubits INTEGER
)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT
        p_qubits
        + (p_qubits * (p_qubits - 1)) / 2
        + p_qubits / 2;
$$;

CREATE OR REPLACE FUNCTION validate_qft_circuit(
    p_circuit_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    circuit_qubits INTEGER;
    actual_count INTEGER;
    expected_count INTEGER;
    invalid_gate_count INTEGER;
BEGIN
    SELECT qubit_count
    INTO circuit_qubits
    FROM circuits
    WHERE circuit_id = p_circuit_id;

    IF circuit_qubits IS NULL THEN
        RAISE EXCEPTION 'Circuit % does not exist', p_circuit_id;
    END IF;

    SELECT COUNT(*)
    INTO actual_count
    FROM circuit_gates
    WHERE circuit_id = p_circuit_id;

    expected_count :=
        qft_expected_gate_count(circuit_qubits);

    IF actual_count <> expected_count THEN
        UPDATE circuits
        SET status = 'REJECTED'
        WHERE circuit_id = p_circuit_id;

        RETURN FALSE;
    END IF;

    SELECT COUNT(*)
    INTO invalid_gate_count
    FROM circuit_gates
    WHERE circuit_id = p_circuit_id
      AND (
          target_qubit >= circuit_qubits
          OR (control_qubit IS NOT NULL
              AND control_qubit >= circuit_qubits)
          OR (second_qubit IS NOT NULL
              AND second_qubit >= circuit_qubits)
      );

    IF invalid_gate_count > 0 THEN
        UPDATE circuits
        SET status = 'REJECTED'
        WHERE circuit_id = p_circuit_id;

        RETURN FALSE;
    END IF;

    UPDATE circuits
    SET status = 'VALIDATED',
        validated_at = CURRENT_TIMESTAMP
    WHERE circuit_id = p_circuit_id;

    RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION start_qft_execution(
    p_circuit_id BIGINT,
    p_state_id BIGINT,
    p_direction TEXT
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_execution_id BIGINT;
    v_status circuit_status;
BEGIN
    IF p_direction NOT IN ('FORWARD', 'INVERSE') THEN
        RAISE EXCEPTION
            'Direction must be FORWARD or INVERSE';
    END IF;

    SELECT status
    INTO v_status
    FROM circuits
    WHERE circuit_id = p_circuit_id;

    IF v_status IS DISTINCT FROM 'VALIDATED'
       AND v_status IS DISTINCT FROM 'EXECUTED' THEN
        RAISE EXCEPTION
            'Circuit % is not validated for execution',
            p_circuit_id;
    END IF;

    INSERT INTO executions (
        circuit_id,
        state_id,
        direction,
        status,
        normalization_error
    )
    VALUES (
        p_circuit_id,
        p_state_id,
        p_direction,
        'ACCEPTED',
        0.0
    )
    RETURNING execution_id INTO v_execution_id;

    RETURN v_execution_id;
END;
$$;

CREATE OR REPLACE FUNCTION complete_qft_execution(
    p_execution_id BIGINT,
    p_reference_error DOUBLE PRECISION
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_circuit_id BIGINT;
BEGIN
    IF p_reference_error < 0 THEN
        RAISE EXCEPTION
            'Reference error cannot be negative';
    END IF;

    SELECT circuit_id
    INTO v_circuit_id
    FROM executions
    WHERE execution_id = p_execution_id
    FOR UPDATE;

    IF v_circuit_id IS NULL THEN
        RAISE EXCEPTION
            'Execution % does not exist',
            p_execution_id;
    END IF;

    UPDATE executions
    SET status = CASE
        WHEN p_reference_error <= 1e-9
            THEN 'COMPLETED'::execution_status
        ELSE 'REJECTED'::execution_status
    END,
    maximum_reference_error = p_reference_error,
    completed_at = CURRENT_TIMESTAMP,
    failure_reason = CASE
        WHEN p_reference_error <= 1e-9 THEN NULL
        ELSE 'Reference transform error exceeded tolerance'
    END
    WHERE execution_id = p_execution_id;

    UPDATE circuits
    SET status = CASE
        WHEN p_reference_error <= 1e-9
            THEN 'EXECUTED'::circuit_status
        ELSE 'REJECTED'::circuit_status
    END
    WHERE circuit_id = v_circuit_id;
END;
$$;

CREATE VIEW qft_circuit_structure AS
SELECT
    c.circuit_id,
    c.circuit_name,
    c.qubit_count,
    c.status,
    cg.gate_position,
    cg.gate_type,
    cg.target_qubit,
    cg.control_qubit,
    cg.second_qubit,
    cg.rotation_angle
FROM circuits c
JOIN circuit_gates cg
    ON cg.circuit_id = c.circuit_id;

CREATE VIEW qft_execution_report AS
SELECT
    e.execution_id,
    c.circuit_name,
    c.qubit_count,
    e.direction,
    e.status,
    e.normalization_error,
    e.maximum_reference_error,
    e.started_at,
    e.completed_at,
    e.failure_reason
FROM executions e
JOIN circuits c
    ON c.circuit_id = e.circuit_id;

-- Construct a 3-qubit QFT circuit.
INSERT INTO circuits (
    circuit_name,
    qubit_count
)
VALUES (
    'qft_3_qubit_reference',
    3
);

-- QFT decomposition:
-- target 0: H, CR(pi/2), CR(pi/4)
-- target 1: H, CR(pi/2)
-- target 2: H
-- output reversal: SWAP(0,2)
INSERT INTO circuit_gates (
    circuit_id,
    gate_position,
    gate_type,
    target_qubit,
    control_qubit,
    second_qubit,
    rotation_angle
)
SELECT
    c.circuit_id,
    v.position,
    v.gate_type::gate_type,
    v.target_qubit,
    v.control_qubit,
    v.second_qubit,
    v.rotation_angle
FROM circuits c
CROSS JOIN (
    VALUES
        (1, 'HADAMARD', 0, NULL::INTEGER, NULL::INTEGER, NULL::DOUBLE PRECISION),
        (2, 'CONTROLLED_PHASE', 0, 1, NULL::INTEGER, pi() / 2),
        (3, 'CONTROLLED_PHASE', 0, 2, NULL::INTEGER, pi() / 4),
        (4, 'HADAMARD', 1, NULL::INTEGER, NULL::INTEGER, NULL::DOUBLE PRECISION),
        (5, 'CONTROLLED_PHASE', 1, 2, NULL::INTEGER, pi() / 2),
        (6, 'HADAMARD', 2, NULL::INTEGER, NULL::INTEGER, NULL::DOUBLE PRECISION),
        (7, 'SWAP', 0, NULL::INTEGER, 2, NULL::DOUBLE PRECISION)
) AS v(
    position,
    gate_type,
    target_qubit,
    control_qubit,
    second_qubit,
    rotation_angle
)
WHERE c.circuit_name = 'qft_3_qubit_reference';

-- Basis state |3> is a concrete computational-basis input.
INSERT INTO basis_states (
    circuit_id,
    basis_index,
    label
)
SELECT
    circuit_id,
    3,
    '|011>'
FROM circuits
WHERE circuit_name = 'qft_3_qubit_reference';

-- Validation is performed transactionally before execution.
BEGIN;

SELECT validate_qft_circuit(circuit_id)
FROM circuits
WHERE circuit_name = 'qft_3_qubit_reference';

COMMIT;

-- Inspect the complete gate sequence and verify the expected count.
SELECT
    circuit_name,
    qubit_count,
    COUNT(*) AS actual_gate_count,
    qft_expected_gate_count(qubit_count) AS expected_gate_count
FROM qft_circuit_structure
GROUP BY
    circuit_name,
    qubit_count
ORDER BY circuit_name;

-- Retrieve the gates in execution order.
SELECT
    gate_position,
    gate_type,
    target_qubit,
    control_qubit,
    second_qubit,
    rotation_angle
FROM qft_circuit_structure
WHERE circuit_name = 'qft_3_qubit_reference'
ORDER BY gate_position;

-- Demonstrate a valid execution record.
BEGIN;

WITH selected_state AS (
    SELECT
        b.state_id,
        b.circuit_id
    FROM basis_states b
    JOIN circuits c
        ON c.circuit_id = b.circuit_id
    WHERE c.circuit_name = 'qft_3_qubit_reference'
      AND b.basis_index = 3
)
SELECT start_qft_execution(
    circuit_id,
    state_id,
    'FORWARD'
)
FROM selected_state;

COMMIT;

-- The first execution receives the returned identity from the sequence.
-- The following update is intentionally explicit so the example remains
-- deterministic when executed as one SQL script.
UPDATE executions
SET normalization_error = 0.0
WHERE execution_id = (
    SELECT MAX(execution_id)
    FROM executions
    WHERE circuit_id = (
        SELECT circuit_id
        FROM circuits
        WHERE circuit_name = 'qft_3_qubit_reference'
    )
);

SELECT complete_qft_execution(
    MAX(execution_id),
    2.1e-12
)
FROM executions
WHERE circuit_id = (
    SELECT circuit_id
    FROM circuits
    WHERE circuit_name = 'qft_3_qubit_reference'
);

-- Record every gate as an auditable execution event.
INSERT INTO execution_gate_events (
    execution_id,
    gate_id
)
SELECT
    e.execution_id,
    cg.gate_id
FROM executions e
JOIN circuit_gates cg
    ON cg.circuit_id = e.circuit_id
WHERE e.execution_id = (
    SELECT MAX(execution_id)
    FROM executions
)
ON CONFLICT DO NOTHING;

-- Aggregated report: circuit complexity and execution state.
SELECT
    c.circuit_name,
    c.qubit_count,
    COUNT(cg.gate_id) AS gate_count,
    COUNT(*) FILTER (
        WHERE cg.gate_type = 'HADAMARD'
    ) AS hadamard_count,
    COUNT(*) FILTER (
        WHERE cg.gate_type = 'CONTROLLED_PHASE'
    ) AS controlled_phase_count,
    COUNT(*) FILTER (
        WHERE cg.gate_type = 'SWAP'
    ) AS swap_count,
    c.status
FROM circuits c
LEFT JOIN circuit_gates cg
    ON cg.circuit_id = c.circuit_id
GROUP BY
    c.circuit_id,
    c.circuit_name,
    c.qubit_count,
    c.status
ORDER BY c.circuit_id;

-- Execution report exposes failed validations and numerical errors.
SELECT *
FROM qft_execution_report
ORDER BY execution_id;

-- A CTE detects gates whose qubit positions violate circuit width.
WITH invalid_gate_candidates AS (
    SELECT
        c.circuit_name,
        c.qubit_count,
        cg.gate_position,
        cg.target_qubit,
        cg.control_qubit,
        cg.second_qubit
    FROM circuits c
    JOIN circuit_gates cg
        ON cg.circuit_id = c.circuit_id
)
SELECT *
FROM invalid_gate_candidates
WHERE target_qubit >= qubit_count
   OR COALESCE(control_qubit, 0) >= qubit_count
   OR COALESCE(second_qubit, 0) >= qubit_count;

-- Controlled-phase inventory demonstrates the logarithmic angle sequence
-- used by the QFT decomposition.
SELECT
    gate_position,
    control_qubit,
    target_qubit,
    rotation_angle,
    round(
        rotation_angle / pi(),
        6
    ) AS angle_in_pi_units
FROM qft_circuit_structure
WHERE gate_type = 'CONTROLLED_PHASE'
ORDER BY gate_position;

-- Transactional failure example. The invalid gate violates the trigger
-- because target qubit 9 does not exist in a 3-qubit circuit.
BEGIN;

DO $$
BEGIN
    BEGIN
        INSERT INTO circuit_gates (
            circuit_id,
            gate_position,
            gate_type,
            target_qubit,
            control_qubit,
            second_qubit,
            rotation_angle
        )
        SELECT
            circuit_id,
            99,
            'HADAMARD',
            9,
            NULL,
            NULL,
            NULL
        FROM circuits
        WHERE circuit_name = 'qft_3_qubit_reference';

        RAISE EXCEPTION
            'Invalid gate unexpectedly passed validation';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Expected invalid-gate rejection: %',
                SQLERRM;
    END;
END;
$$;

ROLLBACK;

-- Final state after validation and successful execution.
SELECT
    circuit_name,
    qubit_count,
    status,
    validated_at
FROM circuits
ORDER BY circuit_id;
