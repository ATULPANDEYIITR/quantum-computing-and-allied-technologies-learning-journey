DROP SCHEMA IF EXISTS superdense_coding_demo CASCADE;
CREATE SCHEMA superdense_coding_demo;
SET search_path TO superdense_coding_demo;

-- PostgreSQL model for a superdense-coding communication service.
-- The schema distinguishes physical quantum resources from logical messages,
-- transmission events, channel errors, and decoded outcomes.

CREATE TABLE communication_party (
    party_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    party_name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('SENDER', 'RECEIVER'))
);

CREATE TABLE entangled_pair (
    pair_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sender_party_id BIGINT NOT NULL REFERENCES communication_party(party_id),
    receiver_party_id BIGINT NOT NULL REFERENCES communication_party(party_id),
    bell_state TEXT NOT NULL DEFAULT 'PHI_PLUS'
        CHECK (bell_state IN ('PHI_PLUS')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMPTZ,
    CHECK (sender_party_id <> receiver_party_id),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);

CREATE TABLE quantum_channel (
    channel_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE,
    noise_probability NUMERIC(6,5) NOT NULL DEFAULT 0
        CHECK (noise_probability >= 0 AND noise_probability <= 1),
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE logical_message (
    message_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_bits CHAR(2) NOT NULL UNIQUE,
    encoding_gate TEXT NOT NULL,
    information_bits SMALLINT NOT NULL DEFAULT 2,
    CHECK (message_bits IN ('00', '01', '10', '11')),
    CHECK (encoding_gate IN ('I', 'X', 'Z', 'ZX')),
    CHECK (information_bits = 2)
);

CREATE TABLE transmission (
    transmission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pair_id BIGINT NOT NULL REFERENCES entangled_pair(pair_id),
    channel_id BIGINT NOT NULL REFERENCES quantum_channel(channel_id),
    message_id BIGINT NOT NULL REFERENCES logical_message(message_id),
    sender_party_id BIGINT NOT NULL REFERENCES communication_party(party_id),
    receiver_party_id BIGINT NOT NULL REFERENCES communication_party(party_id),
    sent_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'CREATED'
        CHECK (status IN ('CREATED', 'ENCODED', 'TRANSMITTED', 'DECODED', 'FAILED')),
    CHECK (sender_party_id <> receiver_party_id),
    CHECK (completed_at IS NULL OR completed_at >= sent_at)
);

CREATE TABLE channel_error (
    error_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transmission_id BIGINT NOT NULL REFERENCES transmission(transmission_id)
        ON DELETE CASCADE,
    error_type TEXT NOT NULL
        CHECK (error_type IN ('X', 'Z', 'XZ')),
    detected BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE decoding_event (
    decoding_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transmission_id BIGINT NOT NULL UNIQUE
        REFERENCES transmission(transmission_id)
        ON DELETE CASCADE,
    bell_basis_decoding BOOLEAN NOT NULL DEFAULT TRUE,
    measured_bits CHAR(2),
    measurement_valid BOOLEAN NOT NULL DEFAULT FALSE,
    decoded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        measured_bits IS NULL
        OR measured_bits IN ('00', '01', '10', '11')
    ),
    CHECK (
        measurement_valid = FALSE
        OR measured_bits IS NOT NULL
    )
);

CREATE TABLE communication_audit (
    audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    transmission_id BIGINT NOT NULL REFERENCES transmission(transmission_id),
    event_type TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX idx_transmission_channel_time
    ON transmission(channel_id, sent_at DESC);

CREATE INDEX idx_transmission_message
    ON transmission(message_id);

CREATE INDEX idx_decoding_measurement
    ON decoding_event(measured_bits);

CREATE INDEX idx_audit_transmission_time
    ON communication_audit(transmission_id, event_time DESC);

INSERT INTO communication_party (party_name, role)
VALUES
    ('Alice', 'SENDER'),
    ('Bob', 'RECEIVER');

INSERT INTO entangled_pair (
    sender_party_id,
    receiver_party_id,
    bell_state
)
SELECT
    sender.party_id,
    receiver.party_id,
    'PHI_PLUS'
FROM communication_party sender
CROSS JOIN communication_party receiver
WHERE sender.party_name = 'Alice'
  AND receiver.party_name = 'Bob';

INSERT INTO quantum_channel (
    channel_name,
    noise_probability,
    active
)
VALUES
    ('Ideal quantum channel', 0.00000, TRUE),
    ('Noisy research channel', 0.15000, TRUE);

INSERT INTO logical_message (
    message_bits,
    encoding_gate
)
VALUES
    ('00', 'I'),
    ('01', 'X'),
    ('10', 'Z'),
    ('11', 'ZX');

-- An ideal transmission for every possible two-bit payload.
INSERT INTO transmission (
    pair_id,
    channel_id,
    message_id,
    sender_party_id,
    receiver_party_id,
    status,
    completed_at
)
SELECT
    pair.pair_id,
    channel.channel_id,
    message.message_id,
    alice.party_id,
    bob.party_id,
    'DECODED',
    CURRENT_TIMESTAMP
FROM entangled_pair pair
JOIN quantum_channel channel
    ON channel.channel_name = 'Ideal quantum channel'
JOIN logical_message message
    ON TRUE
JOIN communication_party alice
    ON alice.party_name = 'Alice'
JOIN communication_party bob
    ON bob.party_name = 'Bob';

-- In an ideal channel, Bell-basis decoding returns the original payload.
INSERT INTO decoding_event (
    transmission_id,
    measured_bits,
    measurement_valid
)
SELECT
    transmission_id,
    lm.message_bits,
    TRUE
FROM transmission t
JOIN logical_message lm
    ON lm.message_id = t.message_id
WHERE t.status = 'DECODED';

INSERT INTO communication_audit (
    transmission_id,
    event_type,
    details
)
SELECT
    transmission_id,
    'DECODED',
    jsonb_build_object(
        'channel', 'Ideal quantum channel',
        'bell_basis_measurement', TRUE
    )
FROM transmission;

-- Demonstrate a noisy transmission whose decoded value is corrupted by X.
INSERT INTO transmission (
    pair_id,
    channel_id,
    message_id,
    sender_party_id,
    receiver_party_id,
    status,
    completed_at
)
SELECT
    pair.pair_id,
    channel.channel_id,
    message.message_id,
    alice.party_id,
    bob.party_id,
    'DECODED',
    CURRENT_TIMESTAMP
FROM entangled_pair pair
JOIN quantum_channel channel
    ON channel.channel_name = 'Noisy research channel'
JOIN logical_message message
    ON message.message_bits = '01'
JOIN communication_party alice
    ON alice.party_name = 'Alice'
JOIN communication_party bob
    ON bob.party_name = 'Bob';

INSERT INTO channel_error (
    transmission_id,
    error_type,
    detected
)
SELECT
    transmission_id,
    'X',
    TRUE
FROM transmission
WHERE channel_id = (
    SELECT channel_id
    FROM quantum_channel
    WHERE channel_name = 'Noisy research channel'
);

-- This measured value intentionally differs from the original message.
-- The relational layer records the observed result rather than pretending
-- that a noisy quantum channel is equivalent to an ideal channel.
INSERT INTO decoding_event (
    transmission_id,
    measured_bits,
    measurement_valid
)
SELECT
    t.transmission_id,
    '11',
    TRUE
FROM transmission t
JOIN quantum_channel qc
    ON qc.channel_id = t.channel_id
WHERE qc.channel_name = 'Noisy research channel';

INSERT INTO communication_audit (
    transmission_id,
    event_type,
    details
)
SELECT
    t.transmission_id,
    'CHANNEL_ERROR',
    jsonb_build_object(
        'error_type', 'X',
        'observed_bits', '11',
        'expected_bits', lm.message_bits
    )
FROM transmission t
JOIN logical_message lm
    ON lm.message_id = t.message_id
JOIN quantum_channel qc
    ON qc.channel_id = t.channel_id
WHERE qc.channel_name = 'Noisy research channel';

-- This view evaluates logical correctness without altering the quantum
-- state itself. It is a database representation of application-level
-- transmission outcomes.
CREATE VIEW transmission_outcomes AS
SELECT
    t.transmission_id,
    lm.message_bits AS sent_bits,
    d.measured_bits,
    t.status,
    qc.channel_name,
    qc.noise_probability,
    EXISTS (
        SELECT 1
        FROM channel_error ce
        WHERE ce.transmission_id = t.transmission_id
    ) AS had_channel_error,
    CASE
        WHEN d.measurement_valid
             AND d.measured_bits = lm.message_bits
        THEN TRUE
        ELSE FALSE
    END AS decoded_correctly
FROM transmission t
JOIN logical_message lm
    ON lm.message_id = t.message_id
JOIN decoding_event d
    ON d.transmission_id = t.transmission_id
JOIN quantum_channel qc
    ON qc.channel_id = t.channel_id;

-- Confirm the four possible logical payloads and their encoding operations.
SELECT
    message_bits,
    encoding_gate,
    information_bits
FROM logical_message
ORDER BY message_bits;

-- Compare successful and unsuccessful decoded transmissions by channel.
SELECT
    channel_name,
    COUNT(*) AS transmissions,
    COUNT(*) FILTER (WHERE decoded_correctly) AS correct_decodings,
    COUNT(*) FILTER (WHERE NOT decoded_correctly) AS incorrect_decodings,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE decoded_correctly)
        / NULLIF(COUNT(*), 0),
        2
    ) AS accuracy_percent
FROM transmission_outcomes
GROUP BY channel_name
ORDER BY channel_name;

-- Identify transmissions where the measured payload differs from Alice's
-- logical payload. This is useful for operational monitoring of noisy links.
SELECT
    transmission_id,
    channel_name,
    sent_bits,
    measured_bits,
    noise_probability,
    had_channel_error
FROM transmission_outcomes
WHERE NOT decoded_correctly
ORDER BY transmission_id;

-- Show the complete event trail for the noisy transmission.
SELECT
    audit.transmission_id,
    audit.event_type,
    audit.event_time,
    audit.details
FROM communication_audit audit
JOIN transmission t
    ON t.transmission_id = audit.transmission_id
JOIN quantum_channel qc
    ON qc.channel_id = t.channel_id
WHERE qc.channel_name = 'Noisy research channel'
ORDER BY audit.event_time, audit.audit_id;

-- Transactional integrity example:
-- a production service should not mark an entangled pair consumed unless the
-- associated transmission has been accepted as a completed communication
-- event. The conditional update makes the state transition explicit.
BEGIN;

WITH completed_transmission AS (
    SELECT pair_id
    FROM transmission
    WHERE status = 'DECODED'
      AND completed_at IS NOT NULL
    ORDER BY transmission_id
    LIMIT 1
)
UPDATE entangled_pair ep
SET consumed_at = CURRENT_TIMESTAMP
FROM completed_transmission ct
WHERE ep.pair_id = ct.pair_id
  AND ep.consumed_at IS NULL;

COMMIT;

-- Inspect resource consumption after the transaction.
SELECT
    pair_id,
    bell_state,
    created_at,
    consumed_at
FROM entangled_pair
ORDER BY pair_id;

-- Integrity demonstrations are represented as executable queries that expose
-- invalid state rather than intentionally aborting the whole setup script.
SELECT
    COUNT(*) AS invalid_message_rows
FROM logical_message
WHERE message_bits NOT IN ('00', '01', '10', '11');

SELECT
    COUNT(*) AS invalid_channel_probabilities
FROM quantum_channel
WHERE noise_probability < 0
   OR noise_probability > 1;

SELECT
    COUNT(*) AS invalid_measurements
FROM decoding_event
WHERE measurement_valid
  AND measured_bits IS NULL;

-- The following query identifies reusable entangled resources that have not
-- yet been consumed by a completed communication transaction.
SELECT
    pair_id,
    sender_party_id,
    receiver_party_id,
    created_at
FROM entangled_pair
WHERE consumed_at IS NULL
ORDER BY created_at;
