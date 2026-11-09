/*
    QUANTUM HARDWARE ARCHITECTURE COMPARISON DATABASE

    PostgreSQL 14+

    Models:
    - Quantum hardware architectures
    - Physical qubit technologies
    - Operating environments
    - Engineering metrics
    - Evidence maturity
    - Comparison criteria
    - Configurable evaluation policies
    - Application requirements
    - Evaluation results
    - Architecture ranking

    All comparison scores are illustrative qualitative
    assessments, not measured experimental benchmarks.
*/

DROP SCHEMA IF EXISTS quantum_hardware CASCADE;

CREATE SCHEMA quantum_hardware;

SET search_path TO quantum_hardware, public;

-- =========================================================
-- 1. DOMAIN TYPES
-- =========================================================

CREATE TYPE architecture_type AS ENUM (
    'superconducting',
    'trapped_ion',
    'neutral_atom',
    'photonic',
    'semiconductor_spin',
    'topological'
);

CREATE TYPE evidence_level AS ENUM (
    'mature',
    'established',
    'developing',
    'experimental'
);

CREATE TYPE evaluation_status AS ENUM (
    'pending',
    'completed',
    'rejected'
);

CREATE TYPE application_type AS ENUM (
    'quantum_simulation',
    'optimization',
    'quantum_networking',
    'error_correction_research',
    'general_purpose'
);

-- =========================================================
-- 2. ARCHITECTURE CATALOGUE
-- =========================================================

CREATE TABLE architectures (
    architecture_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    architecture_code architecture_type NOT NULL UNIQUE,

    architecture_name VARCHAR(100) NOT NULL UNIQUE,

    physical_qubit VARCHAR(250) NOT NULL,

    operating_environment VARCHAR(250) NOT NULL,

    evidence evidence_level NOT NULL,

    description TEXT NOT NULL,

    strengths TEXT[] NOT NULL,

    limitations TEXT[] NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_strengths
        CHECK (CARDINALITY(strengths) > 0),

    CONSTRAINT valid_limitations
        CHECK (CARDINALITY(limitations) > 0)
);

-- =========================================================
-- 3. ENGINEERING METRICS
-- =========================================================

CREATE TABLE architecture_metrics (
    metric_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    architecture_id BIGINT NOT NULL UNIQUE
        REFERENCES architectures(architecture_id)
        ON DELETE CASCADE,

    gate_speed SMALLINT NOT NULL
        CHECK (gate_speed BETWEEN 1 AND 5),

    coherence SMALLINT NOT NULL
        CHECK (coherence BETWEEN 1 AND 5),

    connectivity SMALLINT NOT NULL
        CHECK (connectivity BETWEEN 1 AND 5),

    scalability SMALLINT NOT NULL
        CHECK (scalability BETWEEN 1 AND 5),

    engineering_maturity SMALLINT NOT NULL
        CHECK (engineering_maturity BETWEEN 1 AND 5),

    control_integration SMALLINT NOT NULL
        CHECK (control_integration BETWEEN 1 AND 5),

    error_correction_progress SMALLINT NOT NULL
        CHECK (error_correction_progress BETWEEN 1 AND 5),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 4. COMPARISON POLICIES
-- =========================================================

CREATE TABLE comparison_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    gate_speed_weight NUMERIC(6,5) NOT NULL,
    coherence_weight NUMERIC(6,5) NOT NULL,
    connectivity_weight NUMERIC(6,5) NOT NULL,
    scalability_weight NUMERIC(6,5) NOT NULL,
    engineering_maturity_weight NUMERIC(6,5) NOT NULL,
    control_integration_weight NUMERIC(6,5) NOT NULL,
    error_correction_weight NUMERIC(6,5) NOT NULL,

    active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT nonnegative_weights CHECK (
        gate_speed_weight >= 0 AND
        coherence_weight >= 0 AND
        connectivity_weight >= 0 AND
        scalability_weight >= 0 AND
        engineering_maturity_weight >= 0 AND
        control_integration_weight >= 0 AND
        error_correction_weight >= 0
    ),

    CONSTRAINT weights_total_one CHECK (
        ABS(
            gate_speed_weight +
            coherence_weight +
            connectivity_weight +
            scalability_weight +
            engineering_maturity_weight +
            control_integration_weight +
            error_correction_weight - 1.0
        ) < 0.00001
    )
);

-- =========================================================
-- 5. APPLICATION REQUIREMENTS
-- =========================================================

CREATE TABLE applications (
    application_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_code application_type NOT NULL UNIQUE,

    application_name VARCHAR(150) NOT NULL,

    description TEXT NOT NULL
);

CREATE TABLE application_requirements (
    requirement_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    application_id BIGINT NOT NULL
        REFERENCES applications(application_id)
        ON DELETE CASCADE,

    gate_speed_min SMALLINT NOT NULL DEFAULT 1
        CHECK (gate_speed_min BETWEEN 1 AND 5),

    coherence_min SMALLINT NOT NULL DEFAULT 1
        CHECK (coherence_min BETWEEN 1 AND 5),

    connectivity_min SMALLINT NOT NULL DEFAULT 1
        CHECK (connectivity_min BETWEEN 1 AND 5),

    scalability_min SMALLINT NOT NULL DEFAULT 1
        CHECK (scalability_min BETWEEN 1 AND 5),

    engineering_maturity_min SMALLINT NOT NULL DEFAULT 1
        CHECK (engineering_maturity_min BETWEEN 1 AND 5),

    control_integration_min SMALLINT NOT NULL DEFAULT 1
        CHECK (control_integration_min BETWEEN 1 AND 5),

    error_correction_min SMALLINT NOT NULL DEFAULT 1
        CHECK (error_correction_min BETWEEN 1 AND 5),

    production_evidence_required BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (application_id)
);

-- =========================================================
-- 6. EVALUATION RUNS
-- =========================================================

CREATE TABLE evaluation_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    policy_id BIGINT NOT NULL
        REFERENCES comparison_policies(policy_id),

    application_id BIGINT
        REFERENCES applications(application_id),

    status evaluation_status NOT NULL DEFAULT 'pending',

    evaluation_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    notes TEXT
);

CREATE TABLE evaluation_results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    run_id BIGINT NOT NULL
        REFERENCES evaluation_runs(run_id)
        ON DELETE CASCADE,

    architecture_id BIGINT NOT NULL
        REFERENCES architectures(architecture_id),

    weighted_score NUMERIC(8,4) NOT NULL
        CHECK (weighted_score BETWEEN 1 AND 5),

    eligible BOOLEAN NOT NULL,

    assessment TEXT NOT NULL,

    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (run_id, architecture_id)
);

-- =========================================================
-- 7. SAMPLE ARCHITECTURE DATA
-- =========================================================

INSERT INTO architectures (
    architecture_code,
    architecture_name,
    physical_qubit,
    operating_environment,
    evidence,
    description,
    strengths,
    limitations
)
VALUES
(
    'superconducting',
    'Superconducting',
    'Josephson-junction superconducting circuits',
    'Millikelvin dilution refrigerator',
    'mature',
    'Qubits implemented using superconducting electrical circuits.',
    ARRAY[
        'Fast microwave gate operations',
        'Established fabrication ecosystem',
        'Strong control electronics integration'
    ],
    ARRAY[
        'Cryogenic infrastructure',
        'Coherence limitations',
        'Calibration complexity'
    ]
),
(
    'trapped_ion',
    'Trapped Ion',
    'Electromagnetically confined atomic ions',
    'Ultra-high vacuum and laser systems',
    'established',
    'Qubits encoded in controlled internal states of trapped ions.',
    ARRAY[
        'Long coherence',
        'High-fidelity operations',
        'Flexible interactions'
    ],
    ARRAY[
        'Slower gates',
        'Optical engineering complexity',
        'Register scaling challenges'
    ]
),
(
    'neutral_atom',
    'Neutral Atom',
    'Laser-trapped neutral atoms',
    'Ultra-high vacuum and optical trapping',
    'developing',
    'Qubits encoded in neutral atoms manipulated using optical systems.',
    ARRAY[
        'Large programmable atom arrays',
        'Flexible interaction graphs',
        'Potential scalability'
    ],
    ARRAY[
        'Atom loss',
        'Rydberg-state sensitivity',
        'Gate fidelity challenges'
    ]
),
(
    'photonic',
    'Photonic',
    'Single photons and optical modes',
    'Optical systems; platform-dependent',
    'developing',
    'Quantum information encoded in optical degrees of freedom.',
    ARRAY[
        'Optical networking compatibility',
        'Potential room-temperature operation',
        'Low environmental interaction in suitable modes'
    ],
    ARRAY[
        'Photon loss',
        'Detector requirements',
        'Probabilistic operations in many approaches'
    ]
),
(
    'semiconductor_spin',
    'Semiconductor Spin',
    'Electron or nuclear spin',
    'Cryogenic solid-state device',
    'developing',
    'Qubits implemented using spin states in semiconductor structures.',
    ARRAY[
        'Semiconductor fabrication compatibility',
        'Compact devices',
        'Potential electronic integration'
    ],
    ARRAY[
        'Device variability',
        'Control complexity',
        'Connectivity limitations'
    ]
),
(
    'topological',
    'Topological',
    'Proposed non-Abelian anyonic states',
    'Platform-dependent specialized conditions',
    'experimental',
    'Proposed architecture using topologically protected quantum information.',
    ARRAY[
        'Potential protection against certain local errors'
    ],
    ARRAY[
        'Experimental realization remains difficult',
        'Usable topological qubits remain unproven',
        'Fault-tolerant operation unestablished'
    ]
);

-- =========================================================
-- 8. SAMPLE METRICS
-- =========================================================

INSERT INTO architecture_metrics (
    architecture_id,
    gate_speed,
    coherence,
    connectivity,
    scalability,
    engineering_maturity,
    control_integration,
    error_correction_progress
)
SELECT
    architecture_id,
    CASE architecture_code
        WHEN 'superconducting' THEN 5
        WHEN 'trapped_ion' THEN 2
        WHEN 'neutral_atom' THEN 3
        WHEN 'photonic' THEN 4
        WHEN 'semiconductor_spin' THEN 4
        WHEN 'topological' THEN 2
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 2
        WHEN 'trapped_ion' THEN 5
        WHEN 'neutral_atom' THEN 4
        WHEN 'photonic' THEN 4
        WHEN 'semiconductor_spin' THEN 4
        WHEN 'topological' THEN 5
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 3
        WHEN 'trapped_ion' THEN 4
        WHEN 'neutral_atom' THEN 5
        WHEN 'photonic' THEN 3
        WHEN 'semiconductor_spin' THEN 2
        WHEN 'topological' THEN 2
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 4
        WHEN 'trapped_ion' THEN 3
        WHEN 'neutral_atom' THEN 5
        WHEN 'photonic' THEN 4
        WHEN 'semiconductor_spin' THEN 4
        WHEN 'topological' THEN 3
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 5
        WHEN 'trapped_ion' THEN 4
        WHEN 'neutral_atom' THEN 3
        WHEN 'photonic' THEN 2
        WHEN 'semiconductor_spin' THEN 2
        WHEN 'topological' THEN 1
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 4
        WHEN 'trapped_ion' THEN 3
        WHEN 'neutral_atom' THEN 3
        WHEN 'photonic' THEN 3
        WHEN 'semiconductor_spin' THEN 4
        WHEN 'topological' THEN 1
    END,
    CASE architecture_code
        WHEN 'superconducting' THEN 4
        WHEN 'trapped_ion' THEN 4
        WHEN 'neutral_atom' THEN 3
        WHEN 'photonic' THEN 3
        WHEN 'semiconductor_spin' THEN 2
        WHEN 'topological' THEN 1
    END
FROM architectures;

-- =========================================================
-- 9. SAMPLE COMPARISON POLICY
-- =========================================================

INSERT INTO comparison_policies (
    policy_name,
    gate_speed_weight,
    coherence_weight,
    connectivity_weight,
    scalability_weight,
    engineering_maturity_weight,
    control_integration_weight,
    error_correction_weight
)
VALUES (
    'Balanced Engineering Assessment',
    0.15,
    0.15,
    0.10,
    0.20,
    0.15,
    0.10,
    0.15
);

-- =========================================================
-- 10. APPLICATION DATA
-- =========================================================

INSERT INTO applications (
    application_code,
    application_name,
    description
)
VALUES
(
    'quantum_simulation',
    'Quantum Simulation',
    'Simulation of quantum systems and many-body interactions.'
),
(
    'optimization',
    'Quantum Optimization',
    'Exploration of optimization problems using quantum algorithms.'
),
(
    'quantum_networking',
    'Quantum Networking',
    'Quantum communication and network-connected quantum systems.'
),
(
    'error_correction_research',
    'Quantum Error Correction Research',
    'Experimental study of logical qubits and error-correction protocols.'
),
(
    'general_purpose',
    'General Purpose Quantum Computing',
    'Broad computational capabilities with fault-tolerance objectives.'
);

INSERT INTO application_requirements (
    application_id,
    gate_speed_min,
    coherence_min,
    connectivity_min,
    scalability_min,
    engineering_maturity_min,
    control_integration_min,
    error_correction_min,
    production_evidence_required
)
SELECT
    application_id,
    CASE application_code
        WHEN 'quantum_simulation' THEN 2
        WHEN 'optimization' THEN 3
        WHEN 'quantum_networking' THEN 2
        WHEN 'error_correction_research' THEN 2
        WHEN 'general_purpose' THEN 3
    END,
    CASE application_code
        WHEN 'quantum_simulation' THEN 3
        WHEN 'optimization' THEN 2
        WHEN 'quantum_networking' THEN 3
        WHEN 'error_correction_research' THEN 4
        WHEN 'general_purpose' THEN 4
    END,
    CASE application_code
        WHEN 'quantum_simulation' THEN 3
        WHEN 'optimization' THEN 2
        WHEN 'quantum_networking' THEN 3
        WHEN 'error_correction_research' THEN 3
        WHEN 'general_purpose' THEN 3
    END,
    CASE application_code
        WHEN 'quantum_simulation' THEN 4
        WHEN 'optimization' THEN 3
        WHEN 'quantum_networking' THEN 3
        WHEN 'error_correction_research' THEN 3
        WHEN 'general_purpose' THEN 4
    END,
    2,
    2,
    CASE application_code
        WHEN 'error_correction_research' THEN 3
        WHEN 'general_purpose' THEN 3
        ELSE 2
    END,
    FALSE
FROM applications;

-- =========================================================
-- 11. DATABASE INDEXES
-- =========================================================

CREATE INDEX idx_architectures_evidence
    ON architectures(evidence);

CREATE INDEX idx_metrics_scalability
    ON architecture_metrics(scalability DESC);

CREATE INDEX idx_metrics_coherence
    ON architecture_metrics(coherence DESC);

CREATE INDEX idx_evaluation_runs_status
    ON evaluation_runs(status, evaluation_date DESC);

CREATE INDEX idx_evaluation_results_ranking
    ON evaluation_results(run_id, weighted_score DESC);

CREATE INDEX idx_applications_code
    ON applications(application_code);

-- =========================================================
-- 12. COMPARISON VIEW
-- =========================================================

CREATE VIEW architecture_comparison AS
SELECT
    a.architecture_id,
    a.architecture_code,
    a.architecture_name,
    a.physical_qubit,
    a.operating_environment,
    a.evidence,

    m.gate_speed,
    m.coherence,
    m.connectivity,
    m.scalability,
    m.engineering_maturity,
    m.control_integration,
    m.error_correction_progress,

    ROUND(
        (
            m.gate_speed +
            m.coherence +
            m.connectivity +
            m.scalability +
            m.engineering_maturity +
            m.control_integration +
            m.error_correction_progress
        )::NUMERIC / 7,
        3
    ) AS unweighted_average

FROM architectures a
JOIN architecture_metrics m
    ON a.architecture_id = m.architecture_id;

-- =========================================================
-- 13. WEIGHTED EVALUATION FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION calculate_architecture_score(
    p_architecture_id BIGINT,
    p_policy_id BIGINT
)
RETURNS NUMERIC(8,4)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_score NUMERIC(8,4);
BEGIN
    SELECT
        (
            m.gate_speed * p.gate_speed_weight +
            m.coherence * p.coherence_weight +
            m.connectivity * p.connectivity_weight +
            m.scalability * p.scalability_weight +
            m.engineering_maturity *
                p.engineering_maturity_weight +
            m.control_integration *
                p.control_integration_weight +
            m.error_correction_progress *
                p.error_correction_weight
        )::NUMERIC(8,4)
    INTO v_score
    FROM architecture_metrics m
    CROSS JOIN comparison_policies p
    WHERE
        m.architecture_id = p_architecture_id
        AND p.policy_id = p_policy_id
        AND p.active = TRUE;

    IF v_score IS NULL THEN
        RAISE EXCEPTION
            'Architecture or active policy not found.';
    END IF;

    RETURN v_score;
END;
$$;

-- =========================================================
-- 14. APPLICATION ELIGIBILITY FUNCTION
-- =========================================================

CREATE OR REPLACE FUNCTION check_application_eligibility(
    p_architecture_id BIGINT,
    p_application_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_eligible BOOLEAN;
BEGIN
    SELECT
        m.gate_speed >= r.gate_speed_min
        AND m.coherence >= r.coherence_min
        AND m.connectivity >= r.connectivity_min
        AND m.scalability >= r.scalability_min
        AND m.engineering_maturity >= r.engineering_maturity_min
        AND m.control_integration >= r.control_integration_min
        AND m.error_correction_progress >= r.error_correction_min
        AND (
            NOT r.production_evidence_required
            OR a.evidence IN ('mature', 'established')
        )
    INTO v_eligible
    FROM architecture_metrics m
    JOIN architectures a
        ON a.architecture_id = m.architecture_id
    CROSS JOIN application_requirements r
    WHERE
        m.architecture_id = p_architecture_id
        AND r.application_id = p_application_id;

    IF v_eligible IS NULL THEN
        RAISE EXCEPTION
            'Architecture or application requirements not found.';
    END IF;

    RETURN v_eligible;
END;
$$;

-- =========================================================
-- 15. EVALUATION RESULT AUDIT TRIGGER
-- =========================================================

CREATE TABLE evaluation_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    result_id BIGINT NOT NULL,
    action VARCHAR(30) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_score NUMERIC(8,4),
    new_score NUMERIC(8,4)
);

CREATE OR REPLACE FUNCTION audit_evaluation_result()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO evaluation_audit (
            result_id,
            action,
            new_score
        )
        VALUES (
            NEW.result_id,
            'INSERT',
            NEW.weighted_score
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO evaluation_audit (
            result_id,
            action,
            old_score,
            new_score
        )
        VALUES (
            NEW.result_id,
            'UPDATE',
            OLD.weighted_score,
            NEW.weighted_score
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO evaluation_audit (
            result_id,
            action,
            old_score
        )
        VALUES (
            OLD.result_id,
            'DELETE',
            OLD.weighted_score
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_evaluation_audit
AFTER INSERT OR UPDATE OR DELETE
ON evaluation_results
FOR EACH ROW
EXECUTE FUNCTION audit_evaluation_result();

-- =========================================================
-- 16. EVALUATION PROCEDURE
-- =========================================================

CREATE OR REPLACE PROCEDURE execute_architecture_evaluation(
    p_policy_id BIGINT,
    p_application_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_run_id BIGINT;
    v_architecture RECORD;
    v_score NUMERIC(8,4);
    v_eligible BOOLEAN;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM comparison_policies
        WHERE policy_id = p_policy_id
          AND active = TRUE
    ) THEN
        RAISE EXCEPTION 'Active comparison policy not found.';
    END IF;

    IF p_application_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM applications
            WHERE application_id = p_application_id
       ) THEN
        RAISE EXCEPTION 'Application not found.';
    END IF;

    INSERT INTO evaluation_runs (
        policy_id,
        application_id,
        status,
        notes
    )
    VALUES (
        p_policy_id,
        p_application_id,
        'pending',
        'Weighted architecture evaluation'
    )
    RETURNING run_id INTO v_run_id;

    FOR v_architecture IN
        SELECT architecture_id
        FROM architectures
        ORDER BY architecture_id
    LOOP
        v_score := calculate_architecture_score(
            v_architecture.architecture_id,
            p_policy_id
        );

        IF p_application_id IS NULL THEN
            v_eligible := TRUE;
        ELSE
            v_eligible := check_application_eligibility(
                v_architecture.architecture_id,
                p_application_id
            );
        END IF;

        INSERT INTO evaluation_results (
            run_id,
            architecture_id,
            weighted_score,
            eligible,
            assessment
        )
        VALUES (
            v_run_id,
            v_architecture.architecture_id,
            v_score,
            v_eligible,
            CASE
                WHEN v_eligible THEN
                    'Passes configured evaluation criteria.'
                ELSE
                    'Does not satisfy all configured requirements.'
            END
        );
    END LOOP;

    UPDATE evaluation_runs
    SET status = 'completed'
    WHERE run_id = v_run_id;

    RAISE NOTICE 'Completed evaluation run: %', v_run_id;
END;
$$;

-- =========================================================
-- 17. EXECUTE SAMPLE EVALUATION
-- =========================================================

BEGIN;

CALL execute_architecture_evaluation(
    (
        SELECT policy_id
        FROM comparison_policies
        WHERE policy_name = 'Balanced Engineering Assessment'
    ),
    NULL
);

COMMIT;

-- =========================================================
-- 18. RETRIEVAL QUERY
-- =========================================================

SELECT
    architecture_name,
    physical_qubit,
    operating_environment,
    evidence
FROM architecture_comparison
ORDER BY architecture_name;

-- =========================================================
-- 19. WEIGHTED RANKING
-- =========================================================

SELECT
    r.run_id,
    a.architecture_name,
    er.weighted_score,
    er.eligible,
    er.assessment,
    RANK() OVER (
        PARTITION BY er.run_id
        ORDER BY er.weighted_score DESC
    ) AS ranking
FROM evaluation_results er
JOIN architectures a
    ON a.architecture_id = er.architecture_id
JOIN evaluation_runs r
    ON r.run_id = er.run_id
WHERE r.status = 'completed'
ORDER BY r.run_id, ranking;

-- =========================================================
-- 20. APPLICATION ELIGIBILITY REPORT
-- =========================================================

SELECT
    a.architecture_name,
    ap.application_name,
    check_application_eligibility(
        a.architecture_id,
        ap.application_id
    ) AS eligible
FROM architectures a
CROSS JOIN applications ap
ORDER BY ap.application_name, a.architecture_name;

-- =========================================================
-- 21. AGGREGATION AND REPORTING
-- =========================================================

SELECT
    evidence,
    COUNT(*) AS architecture_count,
    ROUND(AVG(m.scalability), 2) AS average_scalability,
    ROUND(AVG(m.coherence), 2) AS average_coherence,
    ROUND(AVG(m.engineering_maturity), 2)
        AS average_engineering_maturity
FROM architectures a
JOIN architecture_metrics m
    ON a.architecture_id = m.architecture_id
GROUP BY evidence
ORDER BY evidence;

-- =========================================================
-- 22. VALIDATION: INCOMPLETE METRICS
-- =========================================================

SELECT
    a.architecture_name,
    CASE
        WHEN m.architecture_id IS NULL THEN 'Missing metrics'
        ELSE 'Metrics available'
    END AS validation_status
FROM architectures a
LEFT JOIN architecture_metrics m
    ON a.architecture_id = m.architecture_id;

-- =========================================================
-- 23. POLICY AND EVALUATION AUDIT
-- =========================================================

SELECT
    audit_id,
    result_id,
    action,
    changed_at,
    old_score,
    new_score
FROM evaluation_audit
ORDER BY changed_at DESC;

-- =========================================================
-- 24. ADVANCED COMPARISON USING CTE
-- =========================================================

WITH architecture_statistics AS (
    SELECT
        a.architecture_name,
        a.evidence,
        m.gate_speed,
        m.coherence,
        m.connectivity,
        m.scalability,
        m.engineering_maturity,
        m.error_correction_progress,

        (
            m.gate_speed +
            m.coherence +
            m.connectivity +
            m.scalability +
            m.engineering_maturity +
            m.error_correction_progress
        )::NUMERIC / 6 AS engineering_index

    FROM architectures a
    JOIN architecture_metrics m
        ON a.architecture_id = m.architecture_id
),
classified AS (
    SELECT
        *,
        CASE
            WHEN engineering_index >= 4 THEN 'High'
            WHEN engineering_index >= 3 THEN 'Moderate'
            ELSE 'Developing'
        END AS classification
    FROM architecture_statistics
)
SELECT
    architecture_name,
    evidence,
    ROUND(engineering_index, 2) AS engineering_index,
    classification
FROM classified
ORDER BY engineering_index DESC;

-- =========================================================
-- 25. APPLICATION-BASED ELIGIBLE ARCHITECTURES
-- =========================================================

SELECT
    a.architecture_name,
    a.evidence,
    r.weighted_score,
    r.assessment
FROM evaluation_results r
JOIN architectures a
    ON a.architecture_id = r.architecture_id
JOIN evaluation_runs er
    ON er.run_id = r.run_id
WHERE
    er.status = 'completed'
    AND r.eligible = TRUE
ORDER BY r.weighted_score DESC;

-- =========================================================
-- END OF QUANTUM HARDWARE COMPARISON DATABASE
-- =========================================================
