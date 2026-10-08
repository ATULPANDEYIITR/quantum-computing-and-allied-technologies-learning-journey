-- Quantum SDK Landscape
-- PostgreSQL-compatible relational model
--
-- The schema models quantum SDK selection rather than implementing a vendor
-- API. It separates SDK capabilities, workload requirements, circuit
-- characteristics, backend constraints, and recommendation evidence.
--
-- This distinction matters because an SDK can be strong in circuit
-- construction while another is stronger in differentiable programming,
-- compilation, cloud orchestration, accelerated simulation, or resource
-- estimation.

DROP SCHEMA IF EXISTS quantum_sdk_landscape CASCADE;
CREATE SCHEMA quantum_sdk_landscape;
SET search_path TO quantum_sdk_landscape;

CREATE TABLE sdk (
    sdk_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    organization TEXT NOT NULL,
    primary_language TEXT NOT NULL,
    circuit_model TEXT NOT NULL,
    typical_role TEXT NOT NULL,
    differentiable_programming BOOLEAN NOT NULL DEFAULT FALSE,
    compiler_focused BOOLEAN NOT NULL DEFAULT FALSE,
    hardware_access BOOLEAN NOT NULL DEFAULT FALSE,
    simulator_focused BOOLEAN NOT NULL DEFAULT FALSE,
    cloud_orchestration BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT sdk_name_not_blank CHECK (length(trim(name)) > 0)
);

CREATE TABLE sdk_strength (
    sdk_id BIGINT NOT NULL REFERENCES sdk(sdk_id) ON DELETE CASCADE,
    strength TEXT NOT NULL,
    PRIMARY KEY (sdk_id, strength),
    CONSTRAINT strength_not_blank CHECK (length(trim(strength)) > 0)
);

CREATE TABLE sdk_tradeoff (
    sdk_id BIGINT NOT NULL REFERENCES sdk(sdk_id) ON DELETE CASCADE,
    tradeoff TEXT NOT NULL,
    PRIMARY KEY (sdk_id, tradeoff)
);

CREATE TABLE interoperability_target (
    sdk_id BIGINT NOT NULL REFERENCES sdk(sdk_id) ON DELETE CASCADE,
    target_name TEXT NOT NULL,
    PRIMARY KEY (sdk_id, target_name)
);

CREATE TYPE workload_type AS ENUM (
    'general circuit',
    'hardware compilation',
    'quantum machine learning',
    'cloud execution',
    'GPU simulation',
    'resource estimation',
    'research'
);

CREATE TABLE workload (
    workload_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    workload_type workload_type NOT NULL,
    requires_differentiation BOOLEAN NOT NULL DEFAULT FALSE,
    requires_gpu BOOLEAN NOT NULL DEFAULT FALSE,
    requires_cloud BOOLEAN NOT NULL DEFAULT FALSE,
    requires_compiler BOOLEAN NOT NULL DEFAULT FALSE,
    requires_resource_estimation BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NOT NULL
);

CREATE TABLE sdk_workload (
    sdk_id BIGINT NOT NULL REFERENCES sdk(sdk_id) ON DELETE CASCADE,
    workload_id BIGINT NOT NULL REFERENCES workload(workload_id) ON DELETE CASCADE,
    suitability INTEGER NOT NULL,
    rationale TEXT NOT NULL,
    PRIMARY KEY (sdk_id, workload_id),
    CONSTRAINT suitability_range CHECK (suitability BETWEEN 0 AND 100)
);

CREATE TABLE quantum_circuit (
    circuit_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    qubit_count INTEGER NOT NULL,
    gate_count INTEGER NOT NULL DEFAULT 0,
    depth INTEGER NOT NULL DEFAULT 0,
    two_qubit_gate_count INTEGER NOT NULL DEFAULT 0,
    parameterized_gate_count INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT qubit_count_positive CHECK (qubit_count > 0),
    CONSTRAINT gate_count_nonnegative CHECK (gate_count >= 0),
    CONSTRAINT depth_nonnegative CHECK (depth >= 0),
    CONSTRAINT two_qubit_gate_count_nonnegative CHECK (two_qubit_gate_count >= 0),
    CONSTRAINT parameterized_gate_count_nonnegative CHECK (
        parameterized_gate_count >= 0
    ),
    CONSTRAINT depth_not_above_gate_count CHECK (depth <= gate_count),
    CONSTRAINT two_qubit_not_above_gate_count CHECK (
        two_qubit_gate_count <= gate_count
    ),
    CONSTRAINT parameterized_not_above_gate_count CHECK (
        parameterized_gate_count <= gate_count
    )
);

CREATE TYPE backend_kind AS ENUM (
    'simulator',
    'QPU',
    'cloud simulator',
    'hybrid'
);

CREATE TABLE backend (
    backend_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    kind backend_kind NOT NULL,
    qubit_count INTEGER NOT NULL,
    supports_gpu BOOLEAN NOT NULL DEFAULT FALSE,
    supports_dynamic_circuit BOOLEAN NOT NULL DEFAULT FALSE,
    topology_description TEXT NOT NULL,
    CONSTRAINT backend_qubit_count_positive CHECK (qubit_count > 0)
);

CREATE TABLE backend_gate (
    backend_id BIGINT NOT NULL REFERENCES backend(backend_id) ON DELETE CASCADE,
    gate_name TEXT NOT NULL,
    PRIMARY KEY (backend_id, gate_name)
);

CREATE TABLE sdk_backend (
    sdk_id BIGINT NOT NULL REFERENCES sdk(sdk_id) ON DELETE CASCADE,
    backend_id BIGINT NOT NULL REFERENCES backend(backend_id) ON DELETE CASCADE,
    access_mode TEXT NOT NULL,
    PRIMARY KEY (sdk_id, backend_id)
);

CREATE INDEX idx_workload_type
    ON workload(workload_type);

CREATE INDEX idx_sdk_workload_suitability
    ON sdk_workload(suitability DESC);

CREATE INDEX idx_backend_provider
    ON backend(provider);

INSERT INTO sdk (
    name,
    organization,
    primary_language,
    circuit_model,
    typical_role,
    differentiable_programming,
    compiler_focused,
    hardware_access,
    simulator_focused,
    cloud_orchestration
)
VALUES
(
    'Qiskit',
    'IBM',
    'Python',
    'QuantumCircuit with transpilation and primitive-oriented execution',
    'General-purpose circuit development and IBM hardware workflows',
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    TRUE
),
(
    'Cirq',
    'Google Quantum AI',
    'Python',
    'Moment-oriented circuits with explicit qubits and operations',
    'Research and hardware-oriented circuit experimentation',
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
),
(
    'PennyLane',
    'Xanadu',
    'Python',
    'Device-independent quantum functions integrated with autodifferentiation',
    'Quantum machine learning and differentiable hybrid computation',
    TRUE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
),
(
    'pytket / TKET',
    'Quantinuum',
    'Python API with C++ compiler core',
    'Platform-agnostic circuit IR with architecture-aware compilation',
    'Cross-platform circuit compilation and optimization',
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
),
(
    'Amazon Braket SDK',
    'AWS',
    'Python',
    'Provider-neutral circuits and managed quantum tasks',
    'Managed multi-provider cloud quantum workloads',
    FALSE,
    FALSE,
    TRUE,
    TRUE,
    TRUE
),
(
    'CUDA-Q',
    'NVIDIA',
    'C++ and Python',
    'Hybrid quantum-classical kernels and multi-backend execution',
    'High-performance hybrid CPU/GPU/QPU computing',
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    FALSE
),
(
    'Microsoft QDK / Q#',
    'Microsoft',
    'Q# and Python',
    'Hardware-agnostic quantum language with cloud and resource-estimation tooling',
    'Quantum language development and resource estimation',
    FALSE,
    TRUE,
    TRUE,
    TRUE,
    TRUE
);

INSERT INTO sdk_strength (sdk_id, strength)
SELECT sdk_id, strength
FROM sdk
CROSS JOIN LATERAL (
    VALUES
        ('Qiskit', 'circuit construction'),
        ('Qiskit', 'transpilation'),
        ('Qiskit', 'IBM hardware integration'),
        ('Qiskit', 'primitive-oriented execution'),
        ('Cirq', 'moment-oriented circuit representation'),
        ('Cirq', 'hardware-aware research'),
        ('Cirq', 'circuit simulation'),
        ('PennyLane', 'automatic differentiation'),
        ('PennyLane', 'quantum machine learning'),
        ('PennyLane', 'variational algorithms'),
        ('PennyLane', 'hybrid optimization'),
        ('pytket / TKET', 'routing'),
        ('pytket / TKET', 'placement'),
        ('pytket / TKET', 'optimization passes'),
        ('pytket / TKET', 'interoperability'),
        ('Amazon Braket SDK', 'managed cloud execution'),
        ('Amazon Braket SDK', 'multi-provider access'),
        ('Amazon Braket SDK', 'hybrid jobs'),
        ('CUDA-Q', 'GPU-accelerated simulation'),
        ('CUDA-Q', 'hybrid CPU/GPU/QPU workflows'),
        ('CUDA-Q', 'multiple backends'),
        ('Microsoft QDK / Q#', 'Q# language'),
        ('Microsoft QDK / Q#', 'resource estimation'),
        ('Microsoft QDK / Q#', 'simulation'),
        ('Microsoft QDK / Q#', 'Azure Quantum integration')
) AS values(sdk_name, strength)
WHERE sdk.name = values.sdk_name;

INSERT INTO sdk_tradeoff (sdk_id, tradeoff)
SELECT sdk_id, tradeoff
FROM sdk
CROSS JOIN LATERAL (
    VALUES
        ('Qiskit', 'provider-specific execution APIs can evolve independently'),
        ('Qiskit', 'hardware performance depends strongly on transpilation'),
        ('Cirq', 'cloud orchestration is not its primary abstraction'),
        ('Cirq', 'hardware workflows may require Google-specific components'),
        ('PennyLane', 'gradient computation can require additional device executions'),
        ('PennyLane', 'backend capabilities vary'),
        ('pytket / TKET', 'primarily a compiler and interoperability layer'),
        ('pytket / TKET', 'provider integrations can be separate extensions'),
        ('Amazon Braket SDK', 'cloud execution introduces cost and region constraints'),
        ('Amazon Braket SDK', 'provider capabilities are not identical'),
        ('CUDA-Q', 'accelerated infrastructure is needed for its strongest advantages'),
        ('CUDA-Q', 'backend capabilities vary'),
        ('Microsoft QDK / Q#', 'Q# uses a distinct programming model'),
        ('Microsoft QDK / Q#', 'cloud execution requires target and workspace configuration')
) AS values(sdk_name, tradeoff)
WHERE sdk.name = values.sdk_name;

INSERT INTO interoperability_target (sdk_id, target_name)
SELECT sdk_id, target_name
FROM sdk
CROSS JOIN LATERAL (
    VALUES
        ('Qiskit', 'OpenQASM'),
        ('Qiskit', 'pytket'),
        ('Qiskit', 'IBM Quantum'),
        ('Cirq', 'OpenQASM'),
        ('Cirq', 'Qsim'),
        ('Cirq', 'Google Quantum AI'),
        ('PennyLane', 'Qiskit'),
        ('PennyLane', 'Cirq'),
        ('PennyLane', 'Amazon Braket'),
        ('PennyLane', 'JAX'),
        ('PennyLane', 'PyTorch'),
        ('pytket / TKET', 'Qiskit'),
        ('pytket / TKET', 'Cirq'),
        ('pytket / TKET', 'pyQuil'),
        ('pytket / TKET', 'QIR'),
        ('Amazon Braket SDK', 'PennyLane'),
        ('Amazon Braket SDK', 'OpenQASM'),
        ('CUDA-Q', 'QIR'),
        ('CUDA-Q', 'CUDA'),
        ('Microsoft QDK / Q#', 'OpenQASM'),
        ('Microsoft QDK / Q#', 'Qiskit'),
        ('Microsoft QDK / Q#', 'Cirq'),
        ('Microsoft QDK / Q#', 'PennyLane')
) AS values(sdk_name, target_name)
WHERE sdk.name = values.sdk_name;

INSERT INTO workload (
    name,
    workload_type,
    requires_differentiation,
    requires_gpu,
    requires_cloud,
    requires_compiler,
    requires_resource_estimation,
    description
)
VALUES
(
    'Variational quantum model',
    'quantum machine learning',
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    FALSE,
    'A parameterized circuit whose parameters are optimized through a hybrid classical-quantum loop.'
),
(
    'Architecture-aware circuit optimization',
    'hardware compilation',
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    FALSE,
    'A logical circuit must be transformed to satisfy a target device gate set and connectivity.'
),
(
    'Managed multi-provider experiment',
    'cloud execution',
    FALSE,
    FALSE,
    TRUE,
    FALSE,
    FALSE,
    'A workload requires cloud scheduling and access to different simulator or QPU providers.'
),
(
    'GPU-accelerated simulation',
    'GPU simulation',
    FALSE,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    'A simulation workload benefits from GPU-parallel state-vector or tensor-network computation.'
),
(
    'Fault-tolerant resource estimate',
    'resource estimation',
    FALSE,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    'A future algorithm must be evaluated for logical and physical resource requirements.'
);

INSERT INTO sdk_workload (sdk_id, workload_id, suitability, rationale)
SELECT
    sdk.sdk_id,
    workload.workload_id,
    CASE
        WHEN sdk.name = 'PennyLane'
             AND workload.workload_type = 'quantum machine learning'
            THEN 96
        WHEN sdk.name = 'pytket / TKET'
             AND workload.workload_type = 'hardware compilation'
            THEN 97
        WHEN sdk.name = 'Amazon Braket SDK'
             AND workload.workload_type = 'cloud execution'
            THEN 96
        WHEN sdk.name = 'CUDA-Q'
             AND workload.workload_type = 'GPU simulation'
            THEN 98
        WHEN sdk.name = 'Microsoft QDK / Q#'
             AND workload.workload_type = 'resource estimation'
            THEN 98
        WHEN sdk.name = 'Qiskit'
             AND workload.workload_type = 'general circuit'
            THEN 94
        WHEN sdk.name = 'Cirq'
             AND workload.workload_type = 'research'
            THEN 94
        ELSE 70
    END,
    CASE
        WHEN sdk.name = 'PennyLane'
             AND workload.workload_type = 'quantum machine learning'
            THEN 'Differentiable programming is a primary architectural feature.'
        WHEN sdk.name = 'pytket / TKET'
             AND workload.workload_type = 'hardware compilation'
            THEN 'Compilation, placement, routing, and optimization are central responsibilities.'
        WHEN sdk.name = 'Amazon Braket SDK'
             AND workload.workload_type = 'cloud execution'
            THEN 'Managed cloud tasks and hybrid jobs provide the execution layer.'
        WHEN sdk.name = 'CUDA-Q'
             AND workload.workload_type = 'GPU simulation'
            THEN 'GPU-oriented simulation is a core strength.'
        WHEN sdk.name = 'Microsoft QDK / Q#'
             AND workload.workload_type = 'resource estimation'
            THEN 'Resource estimation is a first-class development workflow.'
        ELSE 'The SDK provides meaningful support but is not the primary fit for this workload.'
    END
FROM sdk
CROSS JOIN workload;

INSERT INTO quantum_circuit (
    name,
    qubit_count,
    gate_count,
    depth,
    two_qubit_gate_count,
    parameterized_gate_count
)
VALUES
(
    'Bell pair',
    2,
    2,
    2,
    1,
    0
),
(
    'Three-qubit variational ansatz',
    3,
    5,
    3,
    2,
    3
);

INSERT INTO backend (
    name,
    provider,
    kind,
    qubit_count,
    supports_gpu,
    supports_dynamic_circuit,
    topology_description
)
VALUES
(
    'Reference Statevector Simulator',
    'Local',
    'simulator',
    32,
    FALSE,
    TRUE,
    'Fully connected logical simulation'
),
(
    'GPU Statevector Simulator',
    'NVIDIA-compatible environment',
    'simulator',
    40,
    TRUE,
    TRUE,
    'Fully connected logical simulation with accelerator support'
),
(
    'Illustrative Linear QPU',
    'Research backend',
    'QPU',
    5,
    FALSE,
    FALSE,
    'Linear connectivity: q0-q1-q2-q3-q4'
);

INSERT INTO backend_gate (backend_id, gate_name)
SELECT backend_id, gate_name
FROM backend
CROSS JOIN LATERAL (
    VALUES
        ('Reference Statevector Simulator', 'H'),
        ('Reference Statevector Simulator', 'RX'),
        ('Reference Statevector Simulator', 'RY'),
        ('Reference Statevector Simulator', 'CX'),
        ('GPU Statevector Simulator', 'H'),
        ('GPU Statevector Simulator', 'RX'),
        ('GPU Statevector Simulator', 'RY'),
        ('GPU Statevector Simulator', 'CX'),
        ('Illustrative Linear QPU', 'H'),
        ('Illustrative Linear QPU', 'RX'),
        ('Illustrative Linear QPU', 'RY'),
        ('Illustrative Linear QPU', 'CX')
) AS values(backend_name, gate_name)
WHERE backend.name = values.backend_name;

INSERT INTO sdk_backend (sdk_id, backend_id, access_mode)
SELECT sdk.sdk_id, backend.backend_id, mapping.access_mode
FROM (
    VALUES
        ('Qiskit', 'Reference Statevector Simulator', 'local simulation'),
        ('Qiskit', 'Illustrative Linear QPU', 'provider execution'),
        ('Cirq', 'Reference Statevector Simulator', 'local simulation'),
        ('Cirq', 'Illustrative Linear QPU', 'hardware-oriented workflow'),
        ('PennyLane', 'Reference Statevector Simulator', 'differentiable simulation'),
        ('PennyLane', 'GPU Statevector Simulator', 'accelerated simulation'),
        ('pytket / TKET', 'Illustrative Linear QPU', 'compiled execution'),
        ('Amazon Braket SDK', 'GPU Statevector Simulator', 'managed cloud simulation'),
        ('CUDA-Q', 'GPU Statevector Simulator', 'accelerated local simulation'),
        ('Microsoft QDK / Q#', 'Reference Statevector Simulator', 'local simulation'),
        ('Microsoft QDK / Q#', 'Illustrative Linear QPU', 'cloud-provider workflow')
) AS mapping(sdk_name, backend_name, access_mode)
JOIN sdk ON sdk.name = mapping.sdk_name
JOIN backend ON backend.name = mapping.backend_name;

-- Workload-oriented selection query.
SELECT
    sdk.name,
    sdk.organization,
    workload.name AS workload,
    sdk_workload.suitability,
    sdk_workload.rationale
FROM sdk_workload
JOIN sdk ON sdk.sdk_id = sdk_workload.sdk_id
JOIN workload ON workload.workload_id = sdk_workload.workload_id
WHERE workload.name = 'Variational quantum model'
ORDER BY sdk_workload.suitability DESC, sdk.name;

-- Compare SDK strengths without collapsing different capabilities into one score.
SELECT
    sdk.name,
    sdk.organization,
    sdk.differentiable_programming,
    sdk.compiler_focused,
    sdk.hardware_access,
    sdk.simulator_focused,
    sdk.cloud_orchestration
FROM sdk
ORDER BY sdk.name;

-- Identify GPU-capable execution paths.
SELECT
    sdk.name AS sdk,
    backend.name AS backend,
    backend.provider,
    backend.kind,
    sdk_backend.access_mode
FROM sdk_backend
JOIN sdk ON sdk.sdk_id = sdk_backend.sdk_id
JOIN backend ON backend.backend_id = sdk_backend.backend_id
WHERE backend.supports_gpu = TRUE
ORDER BY sdk.name, backend.name;

-- Identify circuits whose physical width exceeds a backend's capacity.
SELECT
    circuit.name AS circuit,
    circuit.qubit_count,
    backend.name AS backend,
    backend.qubit_count
FROM quantum_circuit circuit
CROSS JOIN backend
WHERE circuit.qubit_count > backend.qubit_count
ORDER BY circuit.name, backend.name;

-- Find workloads where differentiation is explicitly required but an SDK
-- does not advertise a differentiable programming model.
SELECT
    workload.name,
    sdk.name,
    sdk.differentiable_programming
FROM workload
CROSS JOIN sdk
WHERE workload.requires_differentiation = TRUE
ORDER BY workload.name, sdk.name;

-- A transaction demonstrates that workload metadata and suitability scores
-- can be updated atomically.
BEGIN;

UPDATE sdk_workload
SET suitability = LEAST(suitability + 1, 100)
WHERE workload_id = (
    SELECT workload_id
    FROM workload
    WHERE name = 'Architecture-aware circuit optimization'
)
AND sdk_id = (
    SELECT sdk_id
    FROM sdk
    WHERE name = 'pytket / TKET'
);

COMMIT;

-- A CTE produces a ranked view for a cloud-oriented workload.
WITH ranked_cloud_options AS (
    SELECT
        sdk.name,
        sdk.organization,
        sdk_workload.suitability,
        ROW_NUMBER() OVER (
            ORDER BY sdk_workload.suitability DESC, sdk.name
        ) AS rank_position
    FROM sdk_workload
    JOIN sdk ON sdk.sdk_id = sdk_workload.sdk_id
    JOIN workload ON workload.workload_id = sdk_workload.workload_id
    WHERE workload.requires_cloud = TRUE
)
SELECT *
FROM ranked_cloud_options
WHERE rank_position <= 5
ORDER BY rank_position;

-- Database-level integrity example:
-- The following statement would fail because suitability must remain 0..100.
--
-- UPDATE sdk_workload
-- SET suitability = 101
-- WHERE sdk_id = (SELECT sdk_id FROM sdk WHERE name = 'Qiskit')
--   AND workload_id = (
--       SELECT workload_id FROM workload
--       WHERE name = 'Variational quantum model'
--   );
