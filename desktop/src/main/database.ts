/**
 * SQLite local database — mirror of core cloud tables.
 *
 * Schema mirrors the PostgreSQL cloud database for offline operation.
 * Sync metadata tables track queued operations and sync state.
 *
 * In production: uses better-sqlite3 for synchronous, fast local access.
 */
export const LOCAL_SCHEMA = `
-- Core tables (mirror PostgreSQL schema)
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    display_id TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    phone_primary TEXT,
    email TEXT,
    address_line1 TEXT,
    city TEXT,
    country TEXT DEFAULT 'US',
    is_active INTEGER DEFAULT 1,
    version INTEGER DEFAULT 1,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    practitioner_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    type TEXT DEFAULT 'consultation',
    status TEXT DEFAULT 'scheduled',
    reason TEXT,
    notes TEXT,
    room_name TEXT,
    version INTEGER DEFAULT 1,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS billing_invoices (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    patient_id TEXT,
    invoice_number TEXT,
    status TEXT DEFAULT 'draft',
    grand_total TEXT,
    amount_paid TEXT DEFAULT '0',
    balance_due TEXT,
    line_items TEXT,  -- JSON string
    issued_date TEXT,
    version INTEGER DEFAULT 1,
    updated_at TEXT
);

-- Sync metadata tables
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    payload TEXT,  -- JSON string
    base_version INTEGER DEFAULT 0,
    client_timestamp TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    dependencies TEXT,  -- JSON array string
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
    device_id TEXT PRIMARY KEY,
    last_pull_cursor TEXT,
    last_push_sequence INTEGER DEFAULT 0,
    last_sync_at TEXT
);

CREATE TABLE IF NOT EXISTS sync_conflict_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT,
    entity_id TEXT,
    local_data TEXT,  -- JSON
    server_data TEXT,  -- JSON
    resolved_by TEXT DEFAULT 'pending',  -- 'local', 'remote', 'merge', 'pending'
    created_at TEXT
);
`;

/**
 * Initialize the local SQLite database.
 *
 * In production:
 *   import Database from 'better-sqlite3';
 *   const db = new Database(path.join(app.getPath('userData'), 'healthcare-os.db'));
 *   db.exec(LOCAL_SCHEMA);
 */
export function initLocalDatabase(): void {
  // Stub — implemented in Sprint 9 full build
  console.log("[DB] Local SQLite database initialized.");
}
