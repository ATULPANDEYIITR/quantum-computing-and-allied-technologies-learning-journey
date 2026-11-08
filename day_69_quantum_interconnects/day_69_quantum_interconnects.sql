/*
 * QUANTUM INTERCONNECT NETWORK MANAGEMENT
 * ======================================
 *
 * PostgreSQL relational implementation.
 *
 * Models:
 * - Quantum processing nodes
 * - Quantum interconnect channels
 * - Entanglement generation sessions
 * - Fidelity measurements
 * - Quantum routing requests
 * - Entanglement swapping
 * - Qubit resource allocation
 * - Network policies
 * - Processor maintenance
 * - Operational events
 * - Performance reporting
 *
 * Fidelity is represented using a simplified Werner-state model.
 *
 * Target: PostgreSQL 15+
 */

BEGIN;

CREATE SCHEMA IF NOT EXISTS quantum_network;

SET search_path TO quantum_network, public;

-- ============================================================
-- ENUMERATED DOMAIN TYPES
-- ============================================================

CREATE TYPE processor_status AS ENUM (
    'ONLINE',
    'OFFLINE',
    'MAINTENANCE'
);

CREATE TYPE link_status AS ENUM (
    'IDLE',
    'ENTANGLED',
    'DEGRADED',
    'DOWN'
);

CREATE TYPE generation_status AS ENUM (
    'PENDING',
    'SUCCESS',
    'FAILED',
    'EXPIRED'
);

CREATE TYPE route_status AS ENUM (
    'REQUESTED',
    'APPROVED',
    'ACTIVE',
    'COMPLETED',
    'REJECTED',
    'FAILED'
);

CREATE TYPE event_severity AS ENUM (
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL'
);

-- ============================================================
-- PROCESSOR REGISTRY
-- ============================================================

CREATE TABLE quantum_processors (
    processor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    processor_code VARCHAR(40) NOT NULL UNIQUE,

    processor_name VARCHAR(150) NOT NULL,

    location VARCHAR(150) NOT NULL,

    qubit_capacity INTEGER NOT NULL,

    available_qubits INTEGER NOT NULL,

    coherence_time_ms NUMERIC(14, 4) NOT NULL,

    operational_status processor_status NOT NULL
        DEFAULT 'ONLINE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT positive_qubit_capacity
        CHECK (qubit_capacity > 0),

    CONSTRAINT valid_available_qubits
        CHECK (
            available_qubits >= 0
            AND available_qubits <= qubit_capacity
        ),

    CONSTRAINT positive_coherence_time
        CHECK (coherence_time_ms > 0)
);

CREATE INDEX idx_processors_status
ON quantum_processors(operational_status);

-- ============================================================
-- QUANTUM INTERCONNECTS
-- ============================================================

CREATE TABLE quantum_links (
    link_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    link_code VARCHAR(40) NOT NULL UNIQUE,

    source_processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    destination_processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    distance_km NUMERIC(12, 4) NOT NULL,

    generation_probability NUMERIC(8, 6) NOT NULL,

    initial_fidelity NUMERIC(8, 6) NOT NULL,

    current_fidelity NUMERIC(8, 6) NOT NULL DEFAULT 0.0,

    status link_status NOT NULL DEFAULT 'IDLE',

    generation_attempts BIGINT NOT NULL DEFAULT 0,

    successful_generations BIGINT NOT NULL DEFAULT 0,

    failed_generations BIGINT NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT distinct_link_endpoints
        CHECK (
            source_processor_id <> destination_processor_id
        ),

    CONSTRAINT positive_link_distance
        CHECK (distance_km > 0),

    CONSTRAINT valid_generation_probability
        CHECK (
            generation_probability >= 0
            AND generation_probability <= 1
        ),

    CONSTRAINT valid_initial_fidelity
        CHECK (
            initial_fidelity >= 0.25
            AND initial_fidelity <= 1
        ),

    CONSTRAINT valid_current_fidelity
        CHECK (
            current_fidelity >= 0
            AND current_fidelity <= 1
        ),

    CONSTRAINT valid_generation_counters
        CHECK (
            generation_attempts >= 0
            AND successful_generations >= 0
            AND failed_generations >= 0
            AND generation_attempts >=
                successful_generations + failed_generations
        ),

    UNIQUE (
        source_processor_id,
        destination_processor_id
    )
);

CREATE INDEX idx_links_source
ON quantum_links(source_processor_id);

CREATE INDEX idx_links_destination
ON quantum_links(destination_processor_id);

CREATE INDEX idx_links_status_fidelity
ON quantum_links(status, current_fidelity DESC);

-- ============================================================
-- NETWORK POLICIES
-- ============================================================

CREATE TABLE network_policies (
    policy_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    policy_name VARCHAR(120) NOT NULL UNIQUE,

    minimum_fidelity NUMERIC(8, 6) NOT NULL,

    maximum_distance_km NUMERIC(12, 4) NOT NULL,

    require_online_processors BOOLEAN NOT NULL DEFAULT TRUE,

    allow_degraded_links BOOLEAN NOT NULL DEFAULT FALSE,

    maximum_route_hops INTEGER NOT NULL DEFAULT 10,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_policy_fidelity
        CHECK (
            minimum_fidelity >= 0.25
            AND minimum_fidelity <= 1
        ),

    CONSTRAINT valid_policy_distance
        CHECK (maximum_distance_km > 0),

    CONSTRAINT valid_route_hops
        CHECK (maximum_route_hops > 0)
);

-- ============================================================
-- ENTANGLEMENT GENERATION SESSIONS
-- ============================================================

CREATE TABLE entanglement_sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    link_id BIGINT NOT NULL
        REFERENCES quantum_links(link_id),

    attempt_number BIGINT NOT NULL,

    status generation_status NOT NULL DEFAULT 'PENDING',

    achieved_fidelity NUMERIC(8, 6),

    generation_duration_ms NUMERIC(14, 4),

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CONSTRAINT positive_attempt_number
        CHECK (attempt_number > 0),

    CONSTRAINT valid_session_fidelity
        CHECK (
            achieved_fidelity IS NULL
            OR (
                achieved_fidelity >= 0.25
                AND achieved_fidelity <= 1
            )
        ),

    CONSTRAINT valid_generation_duration
        CHECK (
            generation_duration_ms IS NULL
            OR generation_duration_ms >= 0
        ),

    CONSTRAINT completed_session_timestamp
        CHECK (
            status NOT IN ('SUCCESS', 'FAILED', 'EXPIRED')
            OR completed_at IS NOT NULL
        ),

    UNIQUE(link_id, attempt_number)
);

CREATE INDEX idx_sessions_link_status
ON entanglement_sessions(link_id, status);

CREATE INDEX idx_sessions_created
ON entanglement_sessions(created_at DESC);

-- ============================================================
-- FIDELITY MEASUREMENTS
-- ============================================================

CREATE TABLE fidelity_measurements (
    measurement_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    link_id BIGINT NOT NULL
        REFERENCES quantum_links(link_id),

    session_id BIGINT
        REFERENCES entanglement_sessions(session_id),

    fidelity NUMERIC(8, 6) NOT NULL,

    measurement_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    measurement_method VARCHAR(80) NOT NULL,

    CONSTRAINT valid_measurement_fidelity
        CHECK (fidelity >= 0.25 AND fidelity <= 1)
);

CREATE INDEX idx_fidelity_link_time
ON fidelity_measurements(link_id, measurement_time DESC);

-- ============================================================
-- ROUTING REQUESTS
-- ============================================================

CREATE TABLE route_requests (
    route_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    route_code VARCHAR(50) NOT NULL UNIQUE,

    source_processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    destination_processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    policy_id BIGINT NOT NULL
        REFERENCES network_policies(policy_id),

    status route_status NOT NULL DEFAULT 'REQUESTED',

    estimated_fidelity NUMERIC(8, 6),

    estimated_latency_ms NUMERIC(14, 4),

    hop_count INTEGER,

    rejection_reason TEXT,

    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    CONSTRAINT distinct_route_endpoints
        CHECK (
            source_processor_id <> destination_processor_id
        ),

    CONSTRAINT valid_route_fidelity
        CHECK (
            estimated_fidelity IS NULL
            OR (
                estimated_fidelity >= 0.25
                AND estimated_fidelity <= 1
            )
        ),

    CONSTRAINT valid_route_latency
        CHECK (
            estimated_latency_ms IS NULL
            OR estimated_latency_ms >= 0
        ),

    CONSTRAINT valid_hop_count
        CHECK (hop_count IS NULL OR hop_count >= 0)
);

CREATE INDEX idx_route_status_time
ON route_requests(status, requested_at DESC);

CREATE INDEX idx_route_source_destination
ON route_requests(
    source_processor_id,
    destination_processor_id
);

-- ============================================================
-- ROUTE LINK ALLOCATION
-- ============================================================

CREATE TABLE route_links (
    route_id BIGINT NOT NULL
        REFERENCES route_requests(route_id) ON DELETE CASCADE,

    link_id BIGINT NOT NULL
        REFERENCES quantum_links(link_id),

    hop_sequence INTEGER NOT NULL,

    fidelity_at_allocation NUMERIC(8, 6) NOT NULL,

    PRIMARY KEY(route_id, hop_sequence),

    UNIQUE(route_id, link_id),

    CONSTRAINT positive_hop_sequence
        CHECK (hop_sequence > 0),

    CONSTRAINT valid_allocated_fidelity
        CHECK (
            fidelity_at_allocation >= 0.25
            AND fidelity_at_allocation <= 1
        )
);

CREATE INDEX idx_route_links_link
ON route_links(link_id);

-- ============================================================
-- ENTANGLEMENT SWAPPING OPERATIONS
-- ============================================================

CREATE TABLE swapping_operations (
    swap_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    first_link_id BIGINT NOT NULL
        REFERENCES quantum_links(link_id),

    second_link_id BIGINT NOT NULL
        REFERENCES quantum_links(link_id),

    intermediate_processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    input_fidelity_first NUMERIC(8, 6) NOT NULL,

    input_fidelity_second NUMERIC(8, 6) NOT NULL,

    output_fidelity NUMERIC(8, 6) NOT NULL,

    success BOOLEAN NOT NULL,

    execution_time_ms NUMERIC(14, 4),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT distinct_swap_links
        CHECK (first_link_id <> second_link_id),

    CONSTRAINT valid_first_input
        CHECK (
            input_fidelity_first >= 0.25
            AND input_fidelity_first <= 1
        ),

    CONSTRAINT valid_second_input
        CHECK (
            input_fidelity_second >= 0.25
            AND input_fidelity_second <= 1
        ),

    CONSTRAINT valid_output
        CHECK (
            output_fidelity >= 0.25
            AND output_fidelity <= 1
        ),

    CONSTRAINT valid_swap_duration
        CHECK (
            execution_time_ms IS NULL
            OR execution_time_ms >= 0
        )
);

CREATE INDEX idx_swaps_intermediate
ON swapping_operations(intermediate_processor_id);

-- ============================================================
-- RESOURCE RESERVATIONS
-- ============================================================

CREATE TABLE qubit_reservations (
    reservation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    processor_id BIGINT NOT NULL
        REFERENCES quantum_processors(processor_id),

    route_id BIGINT
        REFERENCES route_requests(route_id),

    reserved_qubits INTEGER NOT NULL,

    reservation_active BOOLEAN NOT NULL DEFAULT TRUE,

    reserved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    released_at TIMESTAMPTZ,

    CONSTRAINT positive_reserved_qubits
        CHECK (reserved_qubits > 0),

    CONSTRAINT valid_release_time
        CHECK (
            released_at IS NULL
            OR released_at >= reserved_at
        )
);

CREATE INDEX idx_active_reservations
ON qubit_reservations(processor_id)
WHERE reservation_active = TRUE;

-- ============================================================
-- NETWORK EVENT AUDIT
-- ============================================================

CREATE TABLE network_events (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    processor_id BIGINT
        REFERENCES quantum_processors(processor_id),

    link_id BIGINT
        REFERENCES quantum_links(link_id),

    route_id BIGINT
        REFERENCES route_requests(route_id),

    severity event_severity NOT NULL DEFAULT 'INFO',

    event_type VARCHAR(100) NOT NULL,

    event_description TEXT NOT NULL,

    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_network_events_time
ON network_events(event_time DESC);

CREATE INDEX idx_network_events_severity
ON network_events(severity, event_time DESC);

-- ============================================================
-- UPDATED TIMESTAMP FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_processor_updated_at
BEFORE UPDATE ON quantum_processors
FOR EACH ROW
EXECUTE FUNCTION update_modified_timestamp();

-- ============================================================
-- ENDPOINT VALIDATION FOR SWAPPING
-- ============================================================

CREATE OR REPLACE FUNCTION validate_swap_topology()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    shared_count INTEGER;
    shared_processor BIGINT;
BEGIN
    SELECT COUNT(*), MIN(p.processor_id)
    INTO shared_count, shared_processor
    FROM (
        SELECT source_processor_id AS processor_id
        FROM quantum_links
        WHERE link_id = NEW.first_link_id

        UNION

        SELECT destination_processor_id
        FROM quantum_links
        WHERE link_id = NEW.first_link_id
    ) p
    INNER JOIN (
        SELECT source_processor_id AS processor_id
        FROM quantum_links
        WHERE link_id = NEW.second_link_id

        UNION

        SELECT destination_processor_id
        FROM quantum_links
        WHERE link_id = NEW.second_link_id
    ) q USING (processor_id);

    IF shared_count <> 1 THEN
        RAISE EXCEPTION
            'Entanglement swapping requires exactly one shared processor';
    END IF;

    IF shared_processor <> NEW.intermediate_processor_id THEN
        RAISE EXCEPTION
            'Intermediate processor does not match link topology';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_swap_topology
BEFORE INSERT ON swapping_operations
FOR EACH ROW
EXECUTE FUNCTION validate_swap_topology();

-- ============================================================
-- WERNER-STATE FIDELITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_swapped_fidelity(
    fidelity_a NUMERIC,
    fidelity_b NUMERIC
)
RETURNS NUMERIC
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    IF fidelity_a < 0.25 OR fidelity_a > 1
       OR fidelity_b < 0.25 OR fidelity_b > 1 THEN
        RAISE EXCEPTION 'Invalid input fidelity';
    END IF;

    RETURN (
        fidelity_a * fidelity_b
        + ((1 - fidelity_a) * (1 - fidelity_b)) / 3
    )::NUMERIC(8,6);
END;
$$;

-- ============================================================
-- ENTANGLEMENT GENERATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE generate_entanglement(
    p_link_id BIGINT,
    p_success BOOLEAN,
    p_duration_ms NUMERIC DEFAULT 5.0
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_attempt BIGINT;
    v_fidelity NUMERIC(8,6);
BEGIN
    IF p_duration_ms < 0 THEN
        RAISE EXCEPTION 'Generation duration cannot be negative';
    END IF;

    -- Lock the link to serialize generation state updates.
    SELECT generation_attempts + 1,
           initial_fidelity
    INTO v_attempt, v_fidelity
    FROM quantum_links
    WHERE link_id = p_link_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Quantum link not found';
    END IF;

    IF p_success THEN
        UPDATE quantum_links
        SET generation_attempts = generation_attempts + 1,
            successful_generations = successful_generations + 1,
            current_fidelity = v_fidelity,
            status = 'ENTANGLED'
        WHERE link_id = p_link_id;

        INSERT INTO entanglement_sessions (
            link_id,
            attempt_number,
            status,
            achieved_fidelity,
            generation_duration_ms,
            completed_at
        )
        VALUES (
            p_link_id,
            v_attempt,
            'SUCCESS',
            v_fidelity,
            p_duration_ms,
            NOW()
        );

        INSERT INTO fidelity_measurements (
            link_id,
            fidelity,
            measurement_method
        )
        VALUES (
            p_link_id,
            v_fidelity,
            'SIMULATED_GENERATION'
        );

    ELSE
        UPDATE quantum_links
        SET generation_attempts = generation_attempts + 1,
            failed_generations = failed_generations + 1,
            current_fidelity = 0,
            status = 'IDLE'
        WHERE link_id = p_link_id;

        INSERT INTO entanglement_sessions (
            link_id,
            attempt_number,
            status,
            generation_duration_ms,
            error_message,
            completed_at
        )
        VALUES (
            p_link_id,
            v_attempt,
            'FAILED',
            p_duration_ms,
            'Entanglement generation failed',
            NOW()
        );
    END IF;
END;
$$;

-- ============================================================
-- ROUTE ELIGIBILITY FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION evaluate_route_eligibility(
    p_route_id BIGINT
)
RETURNS TABLE (
    eligible BOOLEAN,
    reason TEXT
)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_route route_requests%ROWTYPE;
    v_policy network_policies%ROWTYPE;
BEGIN
    SELECT *
    INTO v_route
    FROM route_requests
    WHERE route_id = p_route_id;

    IF NOT FOUND THEN
        RETURN QUERY
        SELECT FALSE, 'Route does not exist'::TEXT;
        RETURN;
    END IF;

    SELECT *
    INTO v_policy
    FROM network_policies
    WHERE policy_id = v_route.policy_id;

    IF NOT FOUND OR NOT v_policy.is_active THEN
        RETURN QUERY
        SELECT FALSE, 'Policy is missing or inactive'::TEXT;
        RETURN;
    END IF;

    IF v_route.status = 'REJECTED' THEN
        RETURN QUERY
        SELECT FALSE, 'Route has already been rejected'::TEXT;
        RETURN;
    END IF;

    IF v_route.hop_count IS NULL OR v_route.hop_count = 0 THEN
        RETURN QUERY
        SELECT FALSE, 'Route has no allocated links'::TEXT;
        RETURN;
    END IF;

    IF v_route.hop_count > v_policy.maximum_route_hops THEN
        RETURN QUERY
        SELECT FALSE, 'Maximum hop count exceeded'::TEXT;
        RETURN;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM route_links rl
        JOIN quantum_links ql USING (link_id)
        WHERE rl.route_id = p_route_id
          AND (
              ql.status <> 'ENTANGLED'
              OR rl.fidelity_at_allocation <
                    v_policy.minimum_fidelity
              OR ql.distance_km >
                    v_policy.maximum_distance_km
          )
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Link state or fidelity policy failed'::TEXT;
        RETURN;
    END IF;

    IF v_policy.require_online_processors AND EXISTS (
        SELECT 1
        FROM route_links rl
        JOIN quantum_links ql USING (link_id)
        JOIN quantum_processors qp
          ON qp.processor_id IN (
              ql.source_processor_id,
              ql.destination_processor_id
          )
        WHERE rl.route_id = p_route_id
          AND qp.operational_status <> 'ONLINE'
    ) THEN
        RETURN QUERY
        SELECT FALSE, 'Processor is not online'::TEXT;
        RETURN;
    END IF;

    RETURN QUERY
    SELECT TRUE, 'Route satisfies configured policy'::TEXT;
END;
$$;

-- ============================================================
-- RESOURCE RESERVATION PROCEDURE
-- ============================================================

CREATE OR REPLACE PROCEDURE reserve_qubits(
    p_processor_id BIGINT,
    p_count INTEGER,
    p_route_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_available INTEGER;
    v_status processor_status;
BEGIN
    IF p_count <= 0 THEN
        RAISE EXCEPTION 'Reservation count must be positive';
    END IF;

    SELECT available_qubits, operational_status
    INTO v_available, v_status
    FROM quantum_processors
    WHERE processor_id = p_processor_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Processor not found';
    END IF;

    IF v_status <> 'ONLINE' THEN
        RAISE EXCEPTION 'Processor is not online';
    END IF;

    IF v_available < p_count THEN
        RAISE EXCEPTION 'Insufficient available qubits';
    END IF;

    UPDATE quantum_processors
    SET available_qubits = available_qubits - p_count
    WHERE processor_id = p_processor_id;

    INSERT INTO qubit_reservations (
        processor_id,
        route_id,
        reserved_qubits
    )
    VALUES (
        p_processor_id,
        p_route_id,
        p_count
    );
END;
$$;

-- ============================================================
-- SAMPLE PROCESSORS
-- ============================================================

INSERT INTO quantum_processors (
    processor_code,
    processor_name,
    location,
    qubit_capacity,
    available_qubits,
    coherence_time_ms
)
VALUES
(
    'QPU-NORTH',
    'North Quantum Processing Center',
    'North Research Facility',
    16,
    16,
    100
),
(
    'QPU-CENTRAL',
    'Central Quantum Processing Center',
    'Central Research Facility',
    12,
    12,
    80
),
(
    'QPU-SOUTH',
    'South Quantum Processing Center',
    'South Research Facility',
    16,
    16,
    120
),
(
    'QPU-REMOTE',
    'Remote Quantum Processing Center',
    'Remote Research Facility',
    8,
    8,
    60
);

-- ============================================================
-- SAMPLE QUANTUM LINKS
-- ============================================================

INSERT INTO quantum_links (
    link_code,
    source_processor_id,
    destination_processor_id,
    distance_km,
    generation_probability,
    initial_fidelity
)
SELECT
    v.link_code,
    source.processor_id,
    destination.processor_id,
    v.distance_km,
    v.probability,
    v.fidelity
FROM (
    VALUES
        ('L-NC', 'QPU-NORTH', 'QPU-CENTRAL', 20, 1.0, 0.98),
        ('L-CS', 'QPU-CENTRAL', 'QPU-SOUTH', 30, 1.0, 0.97),
        ('L-NS', 'QPU-NORTH', 'QPU-SOUTH', 65, 1.0, 0.91),
        ('L-SR', 'QPU-SOUTH', 'QPU-REMOTE', 15, 1.0, 0.96),
        ('L-CR', 'QPU-CENTRAL', 'QPU-REMOTE', 45, 0.0, 0.94)
) AS v(
    link_code,
    source_code,
    destination_code,
    distance_km,
    probability,
    fidelity
)
JOIN quantum_processors source
    ON source.processor_code = v.source_code
JOIN quantum_processors destination
    ON destination.processor_code = v.destination_code;

-- ============================================================
-- SAMPLE POLICIES
-- ============================================================

INSERT INTO network_policies (
    policy_name,
    minimum_fidelity,
    maximum_distance_km,
    require_online_processors,
    allow_degraded_links,
    maximum_route_hops
)
VALUES
(
    'STANDARD_QUANTUM_POLICY',
    0.50,
    100,
    TRUE,
    FALSE,
    5
),
(
    'HIGH_FIDELITY_POLICY',
    0.95,
    50,
    TRUE,
    FALSE,
    3
);

-- ============================================================
-- SAMPLE ENTANGLEMENT GENERATION
-- ============================================================

DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            link_id,
            generation_probability
        FROM quantum_links
        ORDER BY link_id
    LOOP
        CALL generate_entanglement(
            r.link_id,
            r.generation_probability = 1.0,
            5.0
        );
    END LOOP;
END;
$$;

-- ============================================================
-- SAMPLE ROUTING REQUEST
-- ============================================================

INSERT INTO route_requests (
    route_code,
    source_processor_id,
    destination_processor_id,
    policy_id,
    status,
    estimated_fidelity,
    estimated_latency_ms,
    hop_count
)
SELECT
    'ROUTE-NORTH-REMOTE',
    source.processor_id,
    destination.processor_id,
    policy.policy_id,
    'REQUESTED',
    0.98 * 0.97 * 0.96,
    65.0 / 200.0,
    3
FROM quantum_processors source
CROSS JOIN quantum_processors destination
CROSS JOIN network_policies policy
WHERE source.processor_code = 'QPU-NORTH'
  AND destination.processor_code = 'QPU-REMOTE'
  AND policy.policy_name = 'STANDARD_QUANTUM_POLICY';

INSERT INTO route_links (
    route_id,
    link_id,
    hop_sequence,
    fidelity_at_allocation
)
SELECT
    route.route_id,
    link.link_id,
    mapping.hop_sequence,
    link.current_fidelity
FROM (
    VALUES
        ('L-NC', 1),
        ('L-CS', 2),
        ('L-SR', 3)
) AS mapping(link_code, hop_sequence)
JOIN quantum_links link
    ON link.link_code = mapping.link_code
CROSS JOIN route_requests route
WHERE route.route_code = 'ROUTE-NORTH-REMOTE'
  AND link.status = 'ENTANGLED';

-- ============================================================
-- SAMPLE ENTANGLEMENT SWAPPING
-- ============================================================

INSERT INTO swapping_operations (
    first_link_id,
    second_link_id,
    intermediate_processor_id,
    input_fidelity_first,
    input_fidelity_second,
    output_fidelity,
    success,
    execution_time_ms
)
SELECT
    first.link_id,
    second.link_id,
    processor.processor_id,
    first.current_fidelity,
    second.current_fidelity,
    calculate_swapped_fidelity(
        first.current_fidelity,
        second.current_fidelity
    ),
    TRUE,
    2.5
FROM quantum_links first
JOIN quantum_links second
    ON first.destination_processor_id =
       second.source_processor_id
JOIN quantum_processors processor
    ON processor.processor_id =
       first.destination_processor_id
WHERE first.link_code = 'L-NC'
  AND second.link_code = 'L-CS'
  AND first.status = 'ENTANGLED'
  AND second.status = 'ENTANGLED';

-- ============================================================
-- OPERATIONAL EVENTS
-- ============================================================

INSERT INTO network_events (
    severity,
    event_type,
    event_description
)
VALUES
(
    'INFO',
    'NETWORK_INITIALIZED',
    'Quantum processor network initialized'
),
(
    'INFO',
    'ENTANGLEMENT_GENERATION',
    'Initial interconnect generation cycle completed'
),
(
    'WARNING',
    'LINK_GENERATION_FAILURE',
    'Remote direct interconnect did not generate entanglement'
);

-- ============================================================
-- REPORTING VIEW: PROCESSOR INVENTORY
-- ============================================================

CREATE OR REPLACE VIEW processor_inventory AS
SELECT
    processor_code,
    processor_name,
    location,
    operational_status,
    qubit_capacity,
    available_qubits,
    qubit_capacity - available_qubits AS occupied_qubits,
    coherence_time_ms
FROM quantum_processors;

-- ============================================================
-- REPORTING VIEW: LINK PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW link_performance AS
SELECT
    ql.link_code,
    source.processor_code AS source_processor,
    destination.processor_code AS destination_processor,
    ql.distance_km,
    ql.status,
    ql.initial_fidelity,
    ql.current_fidelity,
    ql.generation_attempts,
    ql.successful_generations,
    ql.failed_generations,
    ROUND(
        100.0 * ql.successful_generations /
        NULLIF(ql.generation_attempts, 0),
        2
    ) AS generation_success_percentage
FROM quantum_links ql
JOIN quantum_processors source
    ON source.processor_id = ql.source_processor_id
JOIN quantum_processors destination
    ON destination.processor_id =
       ql.destination_processor_id;

-- ============================================================
-- REPORTING VIEW: ROUTE QUALITY
-- ============================================================

CREATE OR REPLACE VIEW route_quality AS
SELECT
    rr.route_code,
    source.processor_code AS source_processor,
    destination.processor_code AS destination_processor,
    rr.status,
    rr.estimated_fidelity,
    rr.estimated_latency_ms,
    rr.hop_count,
    np.policy_name,
    np.minimum_fidelity,
    rr.requested_at
FROM route_requests rr
JOIN quantum_processors source
    ON source.processor_id = rr.source_processor_id
JOIN quantum_processors destination
    ON destination.processor_id =
       rr.destination_processor_id
JOIN network_policies np
    ON np.policy_id = rr.policy_id;

-- ============================================================
-- RETRIEVAL: PROCESSOR CONNECTIVITY
-- ============================================================

SELECT
    ql.link_code,
    source.processor_code AS source,
    destination.processor_code AS destination,
    ql.distance_km,
    ql.status,
    ql.current_fidelity
FROM quantum_links ql
JOIN quantum_processors source
    ON source.processor_id = ql.source_processor_id
JOIN quantum_processors destination
    ON destination.processor_id = ql.destination_processor_id
ORDER BY ql.distance_km;

-- ============================================================
-- RETRIEVAL: ACTIVE ENTANGLEMENT
-- ============================================================

SELECT
    link_code,
    current_fidelity,
    status
FROM quantum_links
WHERE status = 'ENTANGLED'
ORDER BY current_fidelity DESC;

-- ============================================================
-- VALIDATION: FIDELITY THRESHOLD
-- ============================================================

SELECT
    link_code,
    current_fidelity,
    CASE
        WHEN current_fidelity >= 0.95 THEN 'HIGH'
        WHEN current_fidelity >= 0.75 THEN 'MEDIUM'
        WHEN current_fidelity >= 0.50 THEN 'LOW'
        ELSE 'UNUSABLE'
    END AS fidelity_classification
FROM quantum_links
ORDER BY current_fidelity DESC;

-- ============================================================
-- AGGREGATION: GENERATION SUCCESS
-- ============================================================

SELECT
    COUNT(*) AS total_links,
    SUM(generation_attempts) AS total_attempts,
    SUM(successful_generations) AS successful_attempts,
    SUM(failed_generations) AS failed_attempts,
    ROUND(
        100.0 * SUM(successful_generations) /
        NULLIF(SUM(generation_attempts), 0),
        2
    ) AS network_success_percentage
FROM quantum_links;

-- ============================================================
-- EVALUATION: SWAPPING PERFORMANCE
-- ============================================================

SELECT
    swap_id,
    input_fidelity_first,
    input_fidelity_second,
    output_fidelity,
    calculate_swapped_fidelity(
        input_fidelity_first,
        input_fidelity_second
    ) AS recalculated_fidelity,
    success
FROM swapping_operations;

-- ============================================================
-- REPORTING: PROCESSOR RESOURCE UTILIZATION
-- ============================================================

SELECT
    processor_code,
    qubit_capacity,
    available_qubits,
    ROUND(
        100.0 *
        (qubit_capacity - available_qubits) /
        qubit_capacity,
        2
    ) AS utilization_percentage
FROM quantum_processors
ORDER BY utilization_percentage DESC;

-- ============================================================
-- WORKFLOW: ROUTE ELIGIBILITY
-- ============================================================

SELECT
    rr.route_code,
    eligibility.eligible,
    eligibility.reason
FROM route_requests rr
CROSS JOIN LATERAL
    evaluate_route_eligibility(rr.route_id) eligibility;

-- ============================================================
-- CTE: NETWORK CONNECTIVITY SUMMARY
-- ============================================================

WITH link_summary AS (
    SELECT
        source_processor_id AS processor_id,
        COUNT(*) AS connected_links,
        AVG(current_fidelity) AS average_fidelity
    FROM quantum_links
    GROUP BY source_processor_id

    UNION ALL

    SELECT
        destination_processor_id,
        COUNT(*),
        AVG(current_fidelity)
    FROM quantum_links
    GROUP BY destination_processor_id
)
SELECT
    processor.processor_code,
    SUM(summary.connected_links) AS connectivity_count,
    ROUND(AVG(summary.average_fidelity), 6)
        AS average_connected_fidelity
FROM link_summary summary
JOIN quantum_processors processor
    USING (processor_id)
GROUP BY processor.processor_code
ORDER BY connectivity_count DESC;

-- ============================================================
-- TRANSACTION: ATOMIC RESOURCE RESERVATION
-- ============================================================

DO $$
DECLARE
    v_processor_id BIGINT;
BEGIN
    SELECT processor_id
    INTO v_processor_id
    FROM quantum_processors
    WHERE processor_code = 'QPU-CENTRAL';

    CALL reserve_qubits(v_processor_id, 2, NULL);

    RAISE NOTICE
        'Two qubits reserved successfully for central processor';

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE
            'Resource reservation rejected: %',
            SQLERRM;
END;
$$;

-- ============================================================
-- FAILURE CASE: INVALID FIDELITY
-- Demonstrates application-level validation without
-- aborting the entire script.
-- ============================================================

DO $$
BEGIN
    BEGIN
        PERFORM calculate_swapped_fidelity(1.2, 0.9);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Invalid fidelity correctly rejected: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================
-- FAILURE CASE: INSUFFICIENT QUBIT CAPACITY
-- ============================================================

DO $$
DECLARE
    v_processor_id BIGINT;
BEGIN
    SELECT processor_id
    INTO v_processor_id
    FROM quantum_processors
    WHERE processor_code = 'QPU-REMOTE';

    BEGIN
        CALL reserve_qubits(v_processor_id, 1000, NULL);
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE
                'Excessive reservation rejected: %',
                SQLERRM;
    END;
END;
$$;

-- ============================================================
-- FINAL OPERATIONAL REPORT
-- ============================================================

SELECT * FROM processor_inventory;

SELECT * FROM link_performance;

SELECT * FROM route_quality;

SELECT
    severity,
    event_type,
    event_description,
    event_time
FROM network_events
ORDER BY event_time DESC;

COMMIT;
