-- MemoGarden Soil Database Schema
-- PRD v0.7.0 - Personal Information System
--
-- Soil stores immutable Items (facts) and System Relations (structural connections).
-- All data is append-only; modifications create new Items with supersession links.

-- ============================================================================
-- ITEMS TABLE
-- ============================================================================
-- Items represent immutable facts in the timeline.
-- All Item types (Note, Message, Email, ToolCall, EntityDelta, etc.) share this schema.

CREATE TABLE IF NOT EXISTS item (
    -- Identity
    uuid TEXT PRIMARY KEY,              -- "soil_" + uuid4 (e.g., soil_a1b2c3d4-e5f6-7890-abcd-ef1234567890)

    -- Type and timestamps
    _type TEXT NOT NULL,                -- Item type: 'Note', 'Message', 'Email', 'ToolCall', 'EntityDelta', 'SystemEvent'
    realized_at TEXT NOT NULL,          -- ISO 8601 timestamp: when system recorded this item
    canonical_at TEXT NOT NULL,         -- ISO 8601 timestamp: when user says it happened

    -- Integrity and fidelity
    integrity_hash TEXT,                -- SHA256 of content fields (for corruption detection)
    fidelity TEXT NOT NULL DEFAULT 'full',  -- 'full' | 'summary' | 'stub' | 'tombstone'

    -- Supersession (immutable update mechanism)
    superseded_by TEXT,                 -- UUID of Item that supersedes this one
    superseded_at TEXT,                 -- When supersession occurred

    -- Item-specific data (JSON)
    data JSON NOT NULL,                 -- Type-specific fields (e.g., Email.body, Note.description)

    -- Provider-specific metadata (JSON)
    metadata JSON                       -- Provider-specific data (e.g., GMail labels, original headers)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_item_type ON item(_type);
CREATE INDEX IF NOT EXISTS idx_item_realized ON item(realized_at);
CREATE INDEX IF NOT EXISTS idx_item_canonical ON item(canonical_at);
CREATE INDEX IF NOT EXISTS idx_item_fidelity ON item(fidelity);
CREATE INDEX IF NOT EXISTS idx_item_superseded_by ON item(superseded_by);

-- ============================================================================
-- SYSTEM RELATIONS TABLE
-- ============================================================================
-- System relations encode immutable structural facts between Items and Entities.
-- These are permanent records; culling them would change history.

CREATE TABLE IF NOT EXISTS system_relation (
    uuid TEXT PRIMARY KEY,              -- "soil_" + uuid4

    -- Relation type and participants
    kind TEXT NOT NULL,                 -- 'triggers' | 'cites' | 'derives_from' | 'contains' | 'replies_to' | 'continues' | 'supersedes'
    source TEXT NOT NULL,               -- UUID of source Item/Entity
    source_type TEXT NOT NULL,          -- 'item' | 'entity'
    target TEXT NOT NULL,               -- UUID of target Item/Entity
    target_type TEXT NOT NULL,          -- 'item' | 'entity'

    -- Provenance
    created_at INTEGER NOT NULL,        -- Days since epoch (2020-01-01)
    evidence JSON,                      -- {source, confidence, basis, method}
    metadata JSON,                      -- Additional relation-specific data

    -- Prevent duplicate relations
    UNIQUE(kind, source, target)
);

-- Indexes for relation queries
CREATE INDEX IF NOT EXISTS idx_sysrel_source ON system_relation(source);
CREATE INDEX IF NOT EXISTS idx_sysrel_target ON system_relation(target);
CREATE INDEX IF NOT EXISTS idx_sysrel_kind ON system_relation(kind);
CREATE INDEX IF NOT EXISTS idx_sysrel_created_at ON system_relation(created_at);

-- ============================================================================
-- INDEX STRATEGY
-- ============================================================================
-- Functional indexes for critical fields (current approach)
-- Future: May be replaced with separate index layer (Rust hash tables, etc.)
-- Rebuild strategy: DROP INDEX + CREATE INDEX (indexes are derived data)

-- Index for email deduplication (rfc_message_id in data JSON)
CREATE INDEX IF NOT EXISTS idx_item_email_id ON item(json_extract(data, '$.rfc_message_id'));

-- ============================================================================
-- SCHEMA METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS _schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR REPLACE INTO _schema_metadata (key, value) VALUES ('version', '0.7.0');
INSERT OR REPLACE INTO _schema_metadata (key, value) VALUES ('created_at', datetime('now'));

-- Document known item types for reference
INSERT OR REPLACE INTO _schema_metadata (key, value) VALUES
  ('item_types', 'Note,Message,Email,ToolCall,EntityDelta,SystemEvent');

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- View for email items with common fields extracted
CREATE VIEW IF NOT EXISTS email_view AS
SELECT
    uuid,
    _type,
    realized_at,
    canonical_at,
    json_extract(data, '$.rfc_message_id') AS rfc_message_id,
    json_extract(data, '$.from_address') AS from_address,
    json_extract(data, '$.to_addresses') AS to_addresses,
    json_extract(data, '$.subject') AS subject,
    json_extract(metadata, '$.provider') AS provider,
    json_extract(metadata, '$.gmail_thread_id') AS gmail_thread_id
FROM item
WHERE _type = 'Email';

-- View for threading relations
CREATE VIEW IF NOT EXISTS thread_view AS
SELECT
    sr.uuid,
    sr.source AS reply_uuid,
    sr.target AS parent_uuid,
    json_extract(i.data, '$.rfc_message_id') AS parent_message_id,
    json_extract(i.data, '$.subject') AS subject
FROM system_relation sr
JOIN item i ON i.uuid = sr.target
WHERE sr.kind = 'replies_to';
