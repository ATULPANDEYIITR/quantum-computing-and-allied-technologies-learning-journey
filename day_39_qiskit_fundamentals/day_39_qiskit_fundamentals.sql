-- Qiskit Fundamentals: installation and first-circuit experiment log.
-- PostgreSQL 15 or later.
--
-- This database records reproducible quantum-circuit experiments, circuit
-- operations, simulation runs, and measured outcome counts. It is a research
-- record for Qiskit workflows, not a replacement for the Qiskit runtime.
--
-- Qiskit installation occurs in Python:
--   python -m pip install qiskit qiskit-aer
--
-- The schema intentionally stores gates and outcomes separately so circuit
-- definitions remain stable while repeated executions retain their own seeds
-- and shot counts.

BEGIN;

DROP VIEW IF EXISTS experiment_outcome_summary;
DROP TABLE IF EXISTS measurement_counts;
DROP TABLE IF EXISTS experiment_runs;
DROP TABLE IF EXISTS circuit_operations;
DROP TABLE IF EXISTS quantum_circuits;
DROP TABLE IF EXISTS simulation_backends;

CREATE TABLE simulation_backends (
    backend_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    backend_name TEXT NOT NULL UNIQUE,
    backend_kind TEXT NOT NULL
        CHECK (backend_kind IN ('statevector', 'shot_simulator', 'hardware')),
    software_version TEXT,
    supports_statevector BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quantum_circuits (
    circuit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_name TEXT NOT NULL,
    description TEXT NOT NULL,
    qubit_count SMALLINT NOT NULL CHECK (qubit_count BETWEEN 1 AND 30),
    classical_bit_count SMALLINT NOT NULL
        CHECK (classical_bit_count BETWEEN 1 AND 30),
    purpose TEXT NOT NULL
        CHECK (purpose IN ('deterministic', 'superposition', 'entanglement')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (circuit_name)
);

CREATE TABLE circuit_operations (
    circuit_id BIGINT NOT NULL
        REFERENCES quantum_circuits(circuit_id) ON DELETE CASCADE,
    operation_index INTEGER NOT NULL CHECK (operation_index >= 0),
    gate_name TEXT NOT NULL
        CHECK (gate_name IN ('H', 'X', 'CX')),
    control_qubit SMALLINT,
    target_qubit SMALLINT NOT NULL CHECK (target_qubit >= 0),
    PRIMARY KEY (circuit_id, operation_index),
    CHECK (
        (gate_name IN ('H', 'X') AND control_qubit IS NULL)
        OR
        (gate_name = 'CX' AND control_qubit IS NOT NULL
         AND control_qubit >= 0 AND control_qubit <> target_qubit)
    )
);

CREATE TABLE experiment_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    circuit_id BIGINT NOT NULL REFERENCES quantum_circuits(circuit_id),
    backend_id BIGINT NOT NULL REFERENCES simulation_backends(backend_id),
    run_status TEXT NOT NULL
        CHECK (run_status IN ('queued', 'running', 'completed', 'failed')),
    shots INTEGER NOT NULL CHECK (shots BETWEEN 1 AND 100000000),
    random_seed BIGINT,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (run_status = 'failed' AND error_message IS NOT NULL)
        OR
        (run_status <> 'failed' AND error_message IS NULL)
    ),
    CHECK (
        completed_at IS NULL OR
        started_at IS NULL OR
        completed_at >= started_at
    )
);

CREATE TABLE measurement_counts (
    run_id BIGINT NOT NULL
        REFERENCES experiment_runs(run_id) ON DELETE CASCADE,
    outcome_bits TEXT NOT NULL
        CHECK (outcome_bits ~ '^[01]+$'),
    outcome_count INTEGER NOT NULL CHECK (outcome_count >= 0),
    PRIMARY KEY (run_id, outcome_bits)
);

CREATE INDEX experiment_runs_status_created_idx
    ON experiment_runs (run_status, created_at DESC);

CREATE INDEX experiment_runs_circuit_idx
    ON experiment_runs (circuit_id, created_at DESC);

CREATE INDEX measurement_counts_run_idx
    ON measurement_counts (run_id);

INSERT INTO simulation_backends (
    backend_name, backend_kind, software_version, supports_statevector
)
VALUES
    ('AerSimulator', 'shot_simulator', 'record the installed version', TRUE),
    ('StatevectorSimulator', 'statevector', 'record the installed version', TRUE),
    ('QuantumHardware', 'hardware', NULL, FALSE);

INSERT INTO quantum_circuits (
    circuit_name, description, qubit_count, classical_bit_count, purpose
)
VALUES
    (
        'bit_flip',
        'Apply X to |0>, then measure the qubit.',
        1, 1, 'deterministic'
    ),
    (
        'hadamard_superposition',
        'Apply H to |0> and measure in the computational basis.',
        1, 1, 'superposition'
    ),
    (
        'bell_pair',
        'Apply H to qubit 0, then CX from qubit 0 to qubit 1.',
        2, 2, 'entanglement'
    );

INSERT INTO circuit_operations (
    circuit_id, operation_index, gate_name, control_qubit, target_qubit
)
SELECT circuit_id, 0, 'X', NULL, 0
FROM quantum_circuits
WHERE circuit_name = 'bit_flip';

INSERT INTO circuit_operations (
    circuit_id, operation_index, gate_name, control_qubit, target_qubit
)
SELECT circuit_id, 0, 'H', NULL, 0
FROM quantum_circuits
WHERE circuit_name = 'hadamard_superposition';

INSERT INTO circuit_operations (
    circuit_id, operation_index, gate_name, control_qubit, target_qubit
)
SELECT circuit_id, 0, 'H', NULL, 0
FROM quantum_circuits
WHERE circuit_name = 'bell_pair';

INSERT INTO circuit_operations (
    circuit_id, operation_index, gate_name, control_qubit, target_qubit
)
SELECT circuit_id, 1, 'CX', 0, 1
FROM quantum_circuits
WHERE circuit_name = 'bell_pair';

-- Seed data represents plausible observed counts from three independent runs.
-- These counts are example records, not results obtained by executing Qiskit.
INSERT INTO experiment_runs (
    circuit_id, backend_id, run_status, shots, random_seed,
    started_at, completed_at
)
SELECT c.circuit_id, b.backend_id, 'completed', 128, 42,
       CURRENT_TIMESTAMP - INTERVAL '3 minutes',
       CURRENT_TIMESTAMP - INTERVAL '2 minutes'
FROM quantum_circuits c
CROSS JOIN simulation_backends b
WHERE c.circuit_name = 'bit_flip'
  AND b.backend_name = 'AerSimulator';

INSERT INTO measurement_counts (run_id, outcome_bits, outcome_count)
SELECT run_id, '1', 128
FROM experiment_runs
WHERE random_seed = 42 AND shots = 128;

INSERT INTO experiment_runs (
    circuit_id, backend_id, run_status, shots, random_seed,
    started_at, completed_at
)
SELECT c.circuit_id, b.backend_id, 'completed', 4096, 42,
       CURRENT_TIMESTAMP - INTERVAL '2 minutes',
       CURRENT_TIMESTAMP - INTERVAL '1 minute'
FROM quantum_circuits c
CROSS JOIN simulation_backends b
WHERE c.circuit_name = 'hadamard_superposition'
  AND b.backend_name = 'AerSimulator';

INSERT INTO measurement_counts (run_id, outcome_bits, outcome_count)
SELECT run_id, outcomes.outcome_bits, outcomes.outcome_count
FROM experiment_runs r
JOIN quantum_circuits c ON c.circuit_id = r.circuit_id
CROSS JOIN (
    VALUES ('0', 2041), ('1', 2055)
) AS outcomes(outcome_bits, outcome_count)
WHERE c.circuit_name = 'hadamard_superposition'
  AND r.random_seed = 42;

INSERT INTO experiment_runs (
    circuit_id, backend_id, run_status, shots, random_seed,
    started_at, completed_at
)
SELECT c.circuit_id, b.backend_id, 'completed', 4096, 17,
       CURRENT_TIMESTAMP - INTERVAL '1 minute',
       CURRENT_TIMESTAMP
FROM quantum_circuits c
CROSS JOIN simulation_backends b
WHERE c.circuit_name = 'bell_pair'
  AND b.backend_name = 'AerSimulator';

INSERT INTO measurement_counts (run_id, outcome_bits, outcome_count)
SELECT r.run_id, outcomes.outcome_bits, outcomes.outcome_count
FROM experiment_runs r
JOIN quantum_circuits c ON c.circuit_id = r.circuit_id
CROSS JOIN (
    VALUES ('00', 2072), ('11', 2024)
) AS outcomes(outcome_bits, outcome_count)
WHERE c.circuit_name = 'bell_pair'
  AND r.random_seed = 17;

-- A view combines each run's metadata with observed outcome frequencies.
CREATE VIEW experiment_outcome_summary AS
SELECT
    r.run_id,
    c.circuit_name,
    b.backend_name,
    r.run_status,
    r.shots,
    r.random_seed,
    m.outcome_bits,
    m.outcome_count,
    m.outcome_count::NUMERIC / r.shots AS observed_probability
FROM experiment_runs r
JOIN quantum_circuits c ON c.circuit_id = r.circuit_id
JOIN simulation_backends b ON b.backend_id = r.backend_id
LEFT JOIN measurement_counts m ON m.run_id = r.run_id;

-- Review the circuit's ordered operations.
SELECT
    c.circuit_name,
    o.operation_index,
    o.gate_name,
    o.control_qubit,
    o.target_qubit
FROM quantum_circuits c
JOIN circuit_operations o ON o.circuit_id = c.circuit_id
ORDER BY c.circuit_name, o.operation_index;

-- Inspect empirical distributions. Shot noise makes H outcomes approximately,
-- rather than exactly, equally likely.
SELECT
    circuit_name,
    outcome_bits,
    outcome_count,
    ROUND(observed_probability, 4) AS observed_probability
FROM experiment_outcome_summary
WHERE run_status = 'completed'
ORDER BY circuit_name, outcome_bits;

-- Check whether a run has complete outcome accounting.
-- A returned row indicates an accounting discrepancy.
SELECT
    r.run_id,
    c.circuit_name,
    r.shots,
    COALESCE(SUM(m.outcome_count), 0) AS recorded_shots
FROM experiment_runs r
JOIN quantum_circuits c ON c.circuit_id = r.circuit_id
LEFT JOIN measurement_counts m ON m.run_id = r.run_id
WHERE r.run_status = 'completed'
GROUP BY r.run_id, c.circuit_name, r.shots
HAVING COALESCE(SUM(m.outcome_count), 0) <> r.shots;

-- Check Bell-state support. An ideal H-CX circuit measured in the
-- computational basis permits only 00 and 11.
SELECT
    r.run_id,
    m.outcome_bits,
    m.outcome_count
FROM experiment_runs r
JOIN quantum_circuits c ON c.circuit_id = r.circuit_id
JOIN measurement_counts m ON m.run_id = r.run_id
WHERE c.circuit_name = 'bell_pair'
  AND m.outcome_bits NOT IN ('00', '11');

-- Demonstrate constraint enforcement without aborting the main transaction.
-- A savepoint allows the expected invalid insert to be rolled back.
SAVEPOINT invalid_gate_test;

DO $$
BEGIN
    BEGIN
        INSERT INTO circuit_operations (
            circuit_id, operation_index, gate_name,
            control_qubit, target_qubit
        )
        SELECT circuit_id, 99, 'CX', 0, 0
        FROM quantum_circuits
        WHERE circuit_name = 'bell_pair';

        RAISE EXCEPTION 'Invalid controlled-X operation was unexpectedly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE 'Invalid gate correctly rejected by CHECK constraint';
    END;
END;
$$;

ROLLBACK TO SAVEPOINT invalid_gate_test;
RELEASE SAVEPOINT invalid_gate_test;

-- PostgreSQL constraints cannot enforce aggregate counts across multiple rows
-- with a simple CHECK. Production ingestion should write a completed run and
-- all of its counts in one transaction, then validate the sum before commit.
-- The queries above expose incomplete or inconsistent records.

COMMIT;
