DROP SCHEMA IF EXISTS quantum_hardware CASCADE;
CREATE SCHEMA quantum_hardware;

SET search_path = quantum_hardware, public;

CREATE TYPE qubit_technology AS ENUM (
    'superconducting',
    'trapped_ion',
    'neutral_atom',
    'photonic',
    'spin'
);

CREATE TYPE processor_state AS ENUM (
    'offline',
    'initializing',
    'ready',
    'running',
    'fault'
);

CREATE TYPE subsystem_type AS ENUM (
    'cryogenics',
    'vacuum',
    'optical_control',
    'microwave_control',
    'readout',
    'classical_control'
);

CREATE TYPE experiment_state AS ENUM (
    'requested',
    'accepted',
    'rejected',
    'running',
    'completed',
    'failed'
);

CREATE TABLE processor (
    processor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_name TEXT NOT NULL UNIQUE,
    technology qubit_technology NOT NULL,
    state processor_state NOT NULL DEFAULT 'offline',
    manufacturer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE hardware_subsystem (
    subsystem_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_id BIGINT NOT NULL REFERENCES processor(processor_id)
        ON DELETE CASCADE,
    subsystem_type subsystem_type NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    UNIQUE (processor_id, subsystem_type, name)
);

CREATE TABLE subsystem_component (
    component_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subsystem_id BIGINT NOT NULL REFERENCES hardware_subsystem(subsystem_id)
        ON DELETE CASCADE,
    component_name TEXT NOT NULL,
    operating_constraint TEXT,
    UNIQUE (subsystem_id, component_name)
);

CREATE TABLE qubit (
    qubit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_id BIGINT NOT NULL REFERENCES processor(processor_id)
        ON DELETE CASCADE,
    physical_index INTEGER NOT NULL,
    technology qubit_technology NOT NULL,
    frequency_ghz NUMERIC(10, 5),
    coherence_us NUMERIC(14, 3) NOT NULL,
    gate_fidelity NUMERIC(8, 7) NOT NULL,
    readout_fidelity NUMERIC(8, 7) NOT NULL,
    UNIQUE (processor_id, physical_index),
    CHECK (physical_index >= 0),
    CHECK (frequency_ghz IS NULL OR frequency_ghz >= 0),
    CHECK (coherence_us > 0),
    CHECK (gate_fidelity > 0 AND gate_fidelity <= 1),
    CHECK (readout_fidelity > 0 AND readout_fidelity <= 1)
);

CREATE TABLE gate_profile (
    gate_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_id BIGINT NOT NULL REFERENCES processor(processor_id)
        ON DELETE CASCADE,
    gate_name TEXT NOT NULL,
    duration_ns NUMERIC(14, 3) NOT NULL,
    error_rate NUMERIC(8, 7) NOT NULL,
    UNIQUE (processor_id, gate_name),
    CHECK (duration_ns > 0),
    CHECK (error_rate >= 0 AND error_rate < 1)
);

CREATE TABLE environment_measurement (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_id BIGINT NOT NULL REFERENCES processor(processor_id)
        ON DELETE CASCADE,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperature_k NUMERIC(12, 9) NOT NULL,
    pressure_pa NUMERIC(14, 9) NOT NULL,
    cooling_capacity_mw NUMERIC(12, 4) NOT NULL,
    thermal_load_mw NUMERIC(12, 4) NOT NULL,
    readout_available BOOLEAN NOT NULL,
    CHECK (temperature_k >= 0),
    CHECK (pressure_pa >= 0),
    CHECK (cooling_capacity_mw > 0),
    CHECK (thermal_load_mw >= 0),
    CHECK (thermal_load_mw <= cooling_capacity_mw)
);

CREATE TABLE experiment (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    processor_id BIGINT NOT NULL REFERENCES processor(processor_id),
    requester TEXT NOT NULL,
    circuit_depth INTEGER NOT NULL,
    requires_two_qubit_gates BOOLEAN NOT NULL DEFAULT FALSE,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    state experiment_state NOT NULL DEFAULT 'requested',
    decision_reason TEXT,
    estimated_execution_us NUMERIC(16, 4),
    estimated_error NUMERIC(12, 8),
    CHECK (circuit_depth > 0),
    CHECK (estimated_execution_us IS NULL OR estimated_execution_us >= 0),
    CHECK (estimated_error IS NULL OR
           (estimated_error >= 0 AND estimated_error <= 1))
);

CREATE TABLE experiment_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL REFERENCES experiment(experiment_id)
        ON DELETE CASCADE,
    previous_state experiment_state,
    new_state experiment_state NOT NULL,
    event_message TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qubit_processor
    ON qubit(processor_id);

CREATE INDEX idx_environment_processor_time
    ON environment_measurement(processor_id, measured_at DESC);

CREATE INDEX idx_experiment_processor_state
    ON experiment(processor_id, state);

CREATE INDEX idx_experiment_requested
    ON experiment(requested_at DESC);

CREATE OR REPLACE FUNCTION validate_qubit_technology()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    processor_technology qubit_technology;
BEGIN
    SELECT technology
    INTO processor_technology
    FROM processor
    WHERE processor_id = NEW.processor_id;

    IF processor_technology IS NULL THEN
        RAISE EXCEPTION 'Processor % does not exist', NEW.processor_id;
    END IF;

    IF NEW.technology <> processor_technology THEN
        RAISE EXCEPTION
            'Qubit technology % does not match processor technology %',
            NEW.technology,
            processor_technology;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_qubit_technology
BEFORE INSERT OR UPDATE ON qubit
FOR EACH ROW
EXECUTE FUNCTION validate_qubit_technology();

CREATE OR REPLACE FUNCTION record_experiment_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO experiment_event (
            experiment_id,
            previous_state,
            new_state,
            event_message
        )
        VALUES (
            NEW.experiment_id,
            NULL,
            NEW.state,
            'Experiment created'
        );
    ELSIF OLD.state IS DISTINCT FROM NEW.state THEN
        INSERT INTO experiment_event (
            experiment_id,
            previous_state,
            new_state,
            event_message
        )
        VALUES (
            NEW.experiment_id,
            OLD.state,
            NEW.state,
            COALESCE(
                NEW.decision_reason,
                'Experiment state changed'
            )
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_record_experiment_event
AFTER INSERT OR UPDATE OF state ON experiment
FOR EACH ROW
EXECUTE FUNCTION record_experiment_event();

CREATE OR REPLACE FUNCTION evaluate_experiment(
    p_experiment_id BIGINT
)
RETURNS TABLE (
    accepted BOOLEAN,
    reason TEXT,
    execution_us NUMERIC,
    estimated_error NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_processor_id BIGINT;
    v_state processor_state;
    v_depth INTEGER;
    v_requires_two_qubit BOOLEAN;
    v_coherence NUMERIC;
    v_gate_duration NUMERIC;
    v_gate_error NUMERIC;
    v_two_qubit_gate_count INTEGER;
    v_execution NUMERIC;
    v_error NUMERIC;
BEGIN
    SELECT
        e.processor_id,
        e.circuit_depth,
        e.requires_two_qubit_gates,
        p.state
    INTO
        v_processor_id,
        v_depth,
        v_requires_two_qubit,
        v_state
    FROM experiment e
    JOIN processor p
      ON p.processor_id = e.processor_id
    WHERE e.experiment_id = p_experiment_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Experiment % does not exist', p_experiment_id;
    END IF;

    IF v_state <> 'ready' THEN
        RETURN QUERY
        SELECT
            FALSE,
            'Processor is not ready',
            0::NUMERIC,
            0::NUMERIC;
        RETURN;
    END IF;

    SELECT AVG(coherence_us)
    INTO v_coherence
    FROM qubit
    WHERE processor_id = v_processor_id;

    SELECT
        AVG(duration_ns),
        AVG(error_rate)
    INTO
        v_gate_duration,
        v_gate_error
    FROM gate_profile
    WHERE processor_id = v_processor_id;

    SELECT COUNT(*)
    INTO v_two_qubit_gate_count
    FROM gate_profile
    WHERE processor_id = v_processor_id
      AND gate_name ILIKE '%two-qubit%';

    IF v_requires_two_qubit AND v_two_qubit_gate_count = 0 THEN
        RETURN QUERY
        SELECT
            FALSE,
            'Required two-qubit gate profile is unavailable',
            0::NUMERIC,
            0::NUMERIC;
        RETURN;
    END IF;

    v_execution := v_depth * v_gate_duration / 1000.0;

    IF v_execution > v_coherence THEN
        RETURN QUERY
        SELECT
            FALSE,
            'Estimated execution exceeds average coherence budget',
            v_execution,
            0::NUMERIC;
        RETURN;
    END IF;

    v_error := 1 - POWER(
        1 - v_gate_error,
        v_depth
    );

    RETURN QUERY
    SELECT
        TRUE,
        'Experiment satisfies current hardware constraints',
        v_execution,
        v_error;
END;
$$;

CREATE OR REPLACE VIEW processor_hardware_summary AS
SELECT
    p.processor_id,
    p.processor_name,
    p.technology,
    p.state,
    COUNT(DISTINCT q.qubit_id) AS qubit_count,
    ROUND(AVG(q.coherence_us), 3) AS average_coherence_us,
    ROUND(AVG(q.gate_fidelity), 7) AS average_gate_fidelity,
    ROUND(AVG(q.readout_fidelity), 7) AS average_readout_fidelity,
    COUNT(DISTINCT hs.subsystem_id) AS subsystem_count
FROM processor p
LEFT JOIN qubit q
    ON q.processor_id = p.processor_id
LEFT JOIN hardware_subsystem hs
    ON hs.processor_id = p.processor_id
GROUP BY
    p.processor_id,
    p.processor_name,
    p.technology,
    p.state;

CREATE OR REPLACE VIEW experiment_eligibility_report AS
SELECT
    e.experiment_id,
    p.processor_name,
    e.requester,
    e.circuit_depth,
    e.state,
    evaluation.accepted,
    evaluation.reason,
    evaluation.execution_us,
    evaluation.estimated_error
FROM experiment e
JOIN processor p
  ON p.processor_id = e.processor_id
CROSS JOIN LATERAL evaluate_experiment(e.experiment_id) evaluation;

INSERT INTO processor (
    processor_name,
    technology,
    state,
    manufacturer
)
VALUES (
    'QPU-Alpha',
    'superconducting',
    'ready',
    'Example Quantum Systems'
);

INSERT INTO processor (
    processor_name,
    technology,
    state,
    manufacturer
)
VALUES (
    'QPU-Ion-01',
    'trapped_ion',
    'ready',
    'Example Ion Systems'
);

INSERT INTO hardware_subsystem (
    processor_id,
    subsystem_type,
    name,
    description
)
SELECT
    processor_id,
    'cryogenics',
    'Dilution refrigeration',
    'Provides millikelvin cooling for the superconducting processor'
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO hardware_subsystem (
    processor_id,
    subsystem_type,
    name,
    description
)
SELECT
    processor_id,
    'microwave_control',
    'Microwave control chain',
    'Generates calibrated pulses for qubit manipulation'
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO hardware_subsystem (
    processor_id,
    subsystem_type,
    name,
    description
)
SELECT
    processor_id,
    'readout',
    'Quantum readout',
    'Converts qubit states into classical measurement signals'
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO hardware_subsystem (
    processor_id,
    subsystem_type,
    name,
    description
)
SELECT
    processor_id,
    'classical_control',
    'FPGA control',
    'Provides deterministic timing and experiment control'
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'dilution refrigerator',
    'limited cooling power'
FROM hardware_subsystem
WHERE name = 'Dilution refrigeration';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'mixing chamber',
    'thermalization time'
FROM hardware_subsystem
WHERE name = 'Dilution refrigeration';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'microwave source',
    'phase noise'
FROM hardware_subsystem
WHERE name = 'Microwave control chain';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'IQ mixer',
    'pulse distortion'
FROM hardware_subsystem
WHERE name = 'Microwave control chain';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'quantum-limited amplifier',
    'gain stability'
FROM hardware_subsystem
WHERE name = 'Quantum readout';

INSERT INTO subsystem_component (
    subsystem_id,
    component_name,
    operating_constraint
)
SELECT
    subsystem_id,
    'FPGA controller',
    'control latency'
FROM hardware_subsystem
WHERE name = 'FPGA control';

INSERT INTO qubit (
    processor_id,
    physical_index,
    technology,
    frequency_ghz,
    coherence_us,
    gate_fidelity,
    readout_fidelity
)
SELECT
    p.processor_id,
    gs.i,
    'superconducting',
    5.0 + gs.i * 0.03,
    85.0 - gs.i * 2.0,
    0.9990 - gs.i * 0.00002,
    0.985
FROM processor p
CROSS JOIN generate_series(0, 7) AS gs(i)
WHERE p.processor_name = 'QPU-Alpha';

INSERT INTO qubit (
    processor_id,
    physical_index,
    technology,
    frequency_ghz,
    coherence_us,
    gate_fidelity,
    readout_fidelity
)
SELECT
    p.processor_id,
    gs.i,
    'trapped_ion',
    NULL,
    1000000,
    0.9995,
    0.997
FROM processor p
CROSS JOIN generate_series(0, 3) AS gs(i)
WHERE p.processor_name = 'QPU-Ion-01';

INSERT INTO gate_profile (
    processor_id,
    gate_name,
    duration_ns,
    error_rate
)
SELECT
    processor_id,
    x.gate_name,
    x.duration_ns,
    x.error_rate
FROM processor
CROSS JOIN (
    VALUES
        ('single-qubit gate', 25.0::NUMERIC, 0.0009::NUMERIC),
        ('two-qubit gate', 220.0::NUMERIC, 0.008::NUMERIC),
        ('measurement', 700.0::NUMERIC, 0.015::NUMERIC)
) AS x(gate_name, duration_ns, error_rate)
WHERE processor_name = 'QPU-Alpha';

INSERT INTO gate_profile (
    processor_id,
    gate_name,
    duration_ns,
    error_rate
)
SELECT
    processor_id,
    x.gate_name,
    x.duration_ns,
    x.error_rate
FROM processor
CROSS JOIN (
    VALUES
        ('single-qubit gate', 1000.0::NUMERIC, 0.0005::NUMERIC),
        ('two-qubit gate', 100000.0::NUMERIC, 0.003::NUMERIC),
        ('measurement', 200000.0::NUMERIC, 0.003::NUMERIC)
) AS x(gate_name, duration_ns, error_rate)
WHERE processor_name = 'QPU-Ion-01';

INSERT INTO environment_measurement (
    processor_id,
    temperature_k,
    pressure_pa,
    cooling_capacity_mw,
    thermal_load_mw,
    readout_available
)
SELECT
    processor_id,
    0.015,
    0.0000001,
    1.20,
    0.65,
    TRUE
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO environment_measurement (
    processor_id,
    temperature_k,
    pressure_pa,
    cooling_capacity_mw,
    thermal_load_mw,
    readout_available
)
SELECT
    processor_id,
    0.25,
    0.0000001,
    1.20,
    0.65,
    TRUE
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO experiment (
    processor_id,
    requester,
    circuit_depth,
    requires_two_qubit_gates
)
SELECT
    processor_id,
    'research-team',
    100,
    TRUE
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO experiment (
    processor_id,
    requester,
    circuit_depth,
    requires_two_qubit_gates
)
SELECT
    processor_id,
    'verification-team',
    10000,
    TRUE
FROM processor
WHERE processor_name = 'QPU-Alpha';

INSERT INTO experiment (
    processor_id,
    requester,
    circuit_depth,
    requires_two_qubit_gates
)
SELECT
    processor_id,
    'trapped-ion-team',
    50,
    TRUE
FROM processor
WHERE processor_name = 'QPU-Ion-01';

SELECT *
FROM processor_hardware_summary
ORDER BY processor_id;

SELECT
    p.processor_name,
    hs.subsystem_type,
    hs.name,
    sc.component_name,
    sc.operating_constraint
FROM processor p
JOIN hardware_subsystem hs
    ON hs.processor_id = p.processor_id
LEFT JOIN subsystem_component sc
    ON sc.subsystem_id = hs.subsystem_id
ORDER BY p.processor_name, hs.subsystem_type, sc.component_name;

SELECT
    e.experiment_id,
    e.requester,
    e.circuit_depth,
    e.state,
    r.accepted,
    r.reason,
    ROUND(r.execution_us, 3) AS estimated_execution_us,
    ROUND(r.estimated_error, 6) AS estimated_error
FROM experiment e
CROSS JOIN LATERAL evaluate_experiment(e.experiment_id) r
ORDER BY e.experiment_id;

WITH processor_metrics AS (
    SELECT
        p.processor_id,
        p.processor_name,
        AVG(q.coherence_us) AS average_coherence,
        AVG(g.duration_ns) AS average_gate_duration
    FROM processor p
    JOIN qubit q
      ON q.processor_id = p.processor_id
    JOIN gate_profile g
      ON g.processor_id = p.processor_id
    GROUP BY p.processor_id, p.processor_name
)
SELECT
    processor_name,
    ROUND(average_coherence, 2) AS average_coherence_us,
    ROUND(average_gate_duration, 2) AS average_gate_duration_ns,
    FLOOR(
        average_coherence * 1000 /
        NULLIF(average_gate_duration, 0)
    ) AS estimated_sequential_gate_budget
FROM processor_metrics
ORDER BY processor_name;

SELECT
    p.processor_name,
    em.measured_at,
    em.temperature_k,
    em.thermal_load_mw,
    em.cooling_capacity_mw,
    ROUND(
        em.thermal_load_mw /
        NULLIF(em.cooling_capacity_mw, 0),
        4
    ) AS cooling_utilization
FROM processor p
JOIN environment_measurement em
  ON em.processor_id = p.processor_id
ORDER BY em.measured_at DESC;

BEGIN;

UPDATE experiment
SET state = CASE
    WHEN evaluation.accepted THEN 'accepted'::experiment_state
    ELSE 'rejected'::experiment_state
END,
decision_reason = evaluation.reason,
estimated_execution_us = evaluation.execution_us,
estimated_error = evaluation.estimated_error
FROM LATERAL evaluate_experiment(experiment.experiment_id) evaluation
WHERE experiment.state = 'requested';

COMMIT;

SELECT
    experiment_id,
    previous_state,
    new_state,
    event_message,
    event_time
FROM experiment_event
ORDER BY event_time, event_id;
