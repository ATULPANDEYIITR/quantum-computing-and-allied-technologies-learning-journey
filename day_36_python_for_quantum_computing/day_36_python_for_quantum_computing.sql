-- PostgreSQL-compatible SQL model for Python-oriented quantum computing
-- experiments.
--
-- The schema represents experiments, circuits, qubits, operations, quantum
-- states, measurements, and numerical observables. Constraints enforce
-- relationships and basic physical invariants at the database layer.
--
-- This SQL does not attempt to perform complex linear algebra inside
-- PostgreSQL. Numerical state-vector operations remain an application-level
-- responsibility, while PostgreSQL stores validated experiment metadata,
-- amplitudes, results, and reproducible execution records.

DROP SCHEMA IF EXISTS quantum_lab CASCADE;

CREATE SCHEMA quantum_lab;

SET search_path TO quantum_lab;

CREATE TABLE experiments (
    experiment_id BIGSERIAL PRIMARY KEY,
    experiment_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    qubit_count INTEGER NOT NULL
        CHECK (qubit_count BETWEEN 1 AND 20),
    shots INTEGER NOT NULL
        CHECK (shots > 0),
    random_seed BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE circuits (
    circuit_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    circuit_version INTEGER NOT NULL
        CHECK (circuit_version > 0),
    initial_basis_state TEXT NOT NULL,
    UNIQUE (experiment_id, circuit_version),
    CHECK (
        initial_basis_state ~ '^[01]+$'
    )
);

CREATE TABLE qubits (
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    qubit_index INTEGER NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (experiment_id, qubit_index),
    UNIQUE (experiment_id, label)
);

CREATE TABLE gate_operations (
    operation_id BIGSERIAL PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    operation_order INTEGER NOT NULL
        CHECK (operation_order >= 0),
    gate_name TEXT NOT NULL
        CHECK (
            gate_name IN (
                'H',
                'X',
                'Y',
                'Z',
                'S',
                'CNOT',
                'RY'
            )
        ),
    target_qubit INTEGER NOT NULL
        CHECK (target_qubit >= 0),
    control_qubit INTEGER,
    parameter_radians DOUBLE PRECISION,
    UNIQUE (circuit_id, operation_order),
    CHECK (
        gate_name = 'CNOT'
        OR control_qubit IS NULL
    ),
    CHECK (
        gate_name = 'CNOT'
        OR parameter_radians IS NULL
        OR gate_name = 'RY'
    ),
    CHECK (
        gate_name <> 'CNOT'
        OR control_qubit IS NOT NULL
    ),
    CHECK (
        control_qubit IS NULL
        OR control_qubit <> target_qubit
    )
);

CREATE TABLE quantum_states (
    state_id BIGSERIAL PRIMARY KEY,
    circuit_id BIGINT NOT NULL
        REFERENCES circuits(circuit_id)
        ON DELETE CASCADE,
    state_label TEXT NOT NULL,
    dimension INTEGER NOT NULL
        CHECK (
            dimension > 0
            AND (dimension & (dimension - 1)) = 0
        ),
    normalization DOUBLE PRECISION NOT NULL,
    UNIQUE (circuit_id, state_label),
    CHECK (
        normalization > 0.999999
        AND normalization < 1.000001
    )
);

CREATE TABLE state_amplitudes (
    state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id)
        ON DELETE CASCADE,
    basis_index INTEGER NOT NULL
        CHECK (basis_index >= 0),
    real_part DOUBLE PRECISION NOT NULL,
    imaginary_part DOUBLE PRECISION NOT NULL,
    probability DOUBLE PRECISION GENERATED ALWAYS AS (
        real_part * real_part +
        imaginary_part * imaginary_part
    ) STORED,
    PRIMARY KEY (state_id, basis_index),
    CHECK (
        probability >= 0.0
        AND probability <= 1.0 + 1e-9
    )
);

CREATE TABLE measurements (
    measurement_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id)
        ON DELETE CASCADE,
    shots INTEGER NOT NULL
        CHECK (shots > 0),
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE measurement_counts (
    measurement_id BIGINT NOT NULL
        REFERENCES measurements(measurement_id)
        ON DELETE CASCADE,
    basis_state TEXT NOT NULL
        CHECK (basis_state ~ '^[01]+$'),
    count INTEGER NOT NULL
        CHECK (count >= 0),
    PRIMARY KEY (measurement_id, basis_state)
);

CREATE TABLE observables (
    observable_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT NOT NULL
        REFERENCES experiments(experiment_id)
        ON DELETE CASCADE,
    state_id BIGINT NOT NULL
        REFERENCES quantum_states(state_id)
        ON DELETE CASCADE,
    observable_name TEXT NOT NULL
        CHECK (
            observable_name IN (
                'X',
                'Y',
                'Z',
                'XX',
                'ZZ',
                'ENERGY'
            )
        ),
    expectation_real DOUBLE PRECISION NOT NULL,
    expectation_imaginary DOUBLE PRECISION NOT NULL DEFAULT 0,
    UNIQUE (experiment_id, state_id, observable_name)
);

CREATE INDEX idx_circuits_experiment
    ON circuits(experiment_id);

CREATE INDEX idx_gate_operations_circuit_order
    ON gate_operations(circuit_id, operation_order);

CREATE INDEX idx_state_amplitudes_state_probability
    ON state_amplitudes(state_id, probability DESC);

CREATE INDEX idx_measurement_counts_basis_state
    ON measurement_counts(basis_state);

CREATE INDEX idx_observables_experiment
    ON observables(experiment_id);

-- A trigger verifies that a circuit's basis-state width agrees with the
-- configured number of qubits. This keeps malformed experiment metadata
-- from silently entering the numerical workflow.

CREATE OR REPLACE FUNCTION validate_circuit_basis_width()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_qubits INTEGER;
BEGIN
    SELECT qubit_count
    INTO expected_qubits
    FROM experiments
    WHERE experiment_id = NEW.experiment_id;

    IF length(NEW.initial_basis_state) <> expected_qubits THEN
        RAISE EXCEPTION
            'Initial basis state width % does not match % qubits',
            length(NEW.initial_basis_state),
            expected_qubits;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_circuit_basis_width
BEFORE INSERT OR UPDATE ON circuits
FOR EACH ROW
EXECUTE FUNCTION validate_circuit_basis_width();

-- Sample experiment: H followed by CNOT produces a Bell state.

INSERT INTO experiments (
    experiment_name,
    description,
    qubit_count,
    shots,
    random_seed
)
VALUES (
    'bell-state-python-numpy',
    'Two-qubit Bell-state simulation used to connect Python and NumPy with quantum state-vector mathematics.',
    2,
    1000,
    42
);

INSERT INTO qubits (
    experiment_id,
    qubit_index,
    label
)
SELECT
    experiment_id,
    generate_series(0, qubit_count - 1),
    'q' || generate_series(0, qubit_count - 1)
FROM experiments
WHERE experiment_name = 'bell-state-python-numpy';

INSERT INTO circuits (
    experiment_id,
    circuit_version,
    initial_basis_state
)
SELECT
    experiment_id,
    1,
    '00'
FROM experiments
WHERE experiment_name = 'bell-state-python-numpy';

INSERT INTO gate_operations (
    circuit_id,
    operation_order,
    gate_name,
    target_qubit
)
SELECT
    circuit_id,
    0,
    'H',
    0
FROM circuits
WHERE circuit_version = 1;

INSERT INTO gate_operations (
    circuit_id,
    operation_order,
    gate_name,
    target_qubit,
    control_qubit
)
SELECT
    circuit_id,
    1,
    'CNOT',
    1,
    0
FROM circuits
WHERE circuit_version = 1;

INSERT INTO quantum_states (
    circuit_id,
    state_label,
    dimension,
    normalization
)
SELECT
    circuit_id,
    'bell_phi_plus',
    4,
    1.0
FROM circuits
WHERE circuit_version = 1;

-- |Phi+> = (|00> + |11>) / sqrt(2)

INSERT INTO state_amplitudes (
    state_id,
    basis_index,
    real_part,
    imaginary_part
)
SELECT
    state_id,
    values.basis_index,
    values.real_part,
    values.imaginary_part
FROM quantum_states qs
CROSS JOIN (
    VALUES
        (0, 0.7071067811865476, 0.0),
        (1, 0.0, 0.0),
        (2, 0.0, 0.0),
        (3, 0.7071067811865476, 0.0)
) AS values(basis_index, real_part, imaginary_part)
WHERE qs.state_label = 'bell_phi_plus';

INSERT INTO measurements (
    experiment_id,
    state_id,
    shots
)
SELECT
    e.experiment_id,
    qs.state_id,
    e.shots
FROM experiments e
JOIN circuits c
    ON c.experiment_id = e.experiment_id
JOIN quantum_states qs
    ON qs.circuit_id = c.circuit_id
WHERE e.experiment_name = 'bell-state-python-numpy';

INSERT INTO measurement_counts (
    measurement_id,
    basis_state,
    count
)
SELECT
    m.measurement_id,
    values.basis_state,
    values.count
FROM measurements m
CROSS JOIN (
    VALUES
        ('00', 501),
        ('11', 499)
) AS values(basis_state, count);

INSERT INTO observables (
    experiment_id,
    state_id,
    observable_name,
    expectation_real,
    expectation_imaginary
)
SELECT
    e.experiment_id,
    qs.state_id,
    values.observable_name,
    values.expectation_real,
    values.expectation_imaginary
FROM experiments e
JOIN circuits c
    ON c.experiment_id = e.experiment_id
JOIN quantum_states qs
    ON qs.circuit_id = c.circuit_id
CROSS JOIN (
    VALUES
        ('Z', 0.0, 0.0),
        ('XX', 1.0, 0.0),
        ('ZZ', 1.0, 0.0)
) AS values(
    observable_name,
    expectation_real,
    expectation_imaginary
)
WHERE e.experiment_name = 'bell-state-python-numpy';

-- Query the reconstructed state vector.

SELECT
    qs.state_label,
    sa.basis_index,
    lpad(
        sa.basis_index::TEXT,
        e.qubit_count,
        '0'
    ) AS basis_state,
    sa.real_part,
    sa.imaginary_part,
    sa.probability
FROM experiments e
JOIN circuits c
    ON c.experiment_id = e.experiment_id
JOIN quantum_states qs
    ON qs.circuit_id = c.circuit_id
JOIN state_amplitudes sa
    ON sa.state_id = qs.state_id
WHERE e.experiment_name = 'bell-state-python-numpy'
ORDER BY sa.basis_index;

-- Verify numerical normalization directly from stored amplitudes.

SELECT
    qs.state_label,
    SUM(sa.probability) AS probability_sum,
    ABS(SUM(sa.probability) - 1.0) AS normalization_error
FROM quantum_states qs
JOIN state_amplitudes sa
    ON sa.state_id = qs.state_id
GROUP BY qs.state_label
ORDER BY qs.state_label;

-- Identify basis states that are theoretically impossible for Phi+.
-- A non-zero result here would expose an inconsistent stored measurement.

SELECT
    mc.basis_state,
    mc.count
FROM measurement_counts mc
JOIN measurements m
    ON m.measurement_id = mc.measurement_id
JOIN experiments e
    ON e.experiment_id = m.experiment_id
WHERE e.experiment_name = 'bell-state-python-numpy'
  AND mc.basis_state IN ('01', '10')
  AND mc.count > 0;

-- Calculate empirical probabilities from measurement counts.

SELECT
    mc.basis_state,
    mc.count,
    m.shots,
    mc.count::NUMERIC / m.shots AS empirical_probability
FROM measurement_counts mc
JOIN measurements m
    ON m.measurement_id = mc.measurement_id
ORDER BY mc.basis_state;

-- Show the experiment's gate sequence as an ordered circuit description.

SELECT
    e.experiment_name,
    c.circuit_version,
    go.operation_order,
    go.gate_name,
    go.control_qubit,
    go.target_qubit,
    go.parameter_radians
FROM experiments e
JOIN circuits c
    ON c.experiment_id = e.experiment_id
JOIN gate_operations go
    ON go.circuit_id = c.circuit_id
WHERE e.experiment_name = 'bell-state-python-numpy'
ORDER BY
    c.circuit_version,
    go.operation_order;

-- Compare expected and observed Bell-state correlations.

SELECT
    o.observable_name,
    o.expectation_real,
    CASE
        WHEN o.observable_name IN ('XX', 'ZZ')
             AND ABS(o.expectation_real - 1.0) < 0.000001
            THEN 'correlation matches Phi+ expectation'
        WHEN o.observable_name = 'Z'
             AND ABS(o.expectation_real) < 0.000001
            THEN 'single-qubit Z expectation is zero'
        ELSE 'requires numerical investigation'
    END AS interpretation
FROM observables o
JOIN experiments e
    ON e.experiment_id = o.experiment_id
WHERE e.experiment_name = 'bell-state-python-numpy'
ORDER BY o.observable_name;

-- Transactional demonstration:
-- A malformed gate operation is rejected by the CHECK constraints.
-- The transaction rolls back the attempted change.

BEGIN;

INSERT INTO gate_operations (
    circuit_id,
    operation_order,
    gate_name,
    target_qubit,
    control_qubit
)
SELECT
    circuit_id,
    2,
    'CNOT',
    0,
    0
FROM circuits
WHERE circuit_version = 1;

ROLLBACK;

-- A practical aggregate showing the number of operations and measured shots.

SELECT
    e.experiment_name,
    e.qubit_count,
    COUNT(DISTINCT go.operation_id) AS gate_operations,
    COALESCE(SUM(DISTINCT m.shots), 0) AS recorded_shots
FROM experiments e
LEFT JOIN circuits c
    ON c.experiment_id = e.experiment_id
LEFT JOIN gate_operations go
    ON go.circuit_id = c.circuit_id
LEFT JOIN measurements m
    ON m.experiment_id = e.experiment_id
GROUP BY
    e.experiment_id,
    e.experiment_name,
    e.qubit_count;
