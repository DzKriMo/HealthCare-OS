/**
 * Healthcare OS — Local SQLite database (main process).
 *
 * Uses sql.js (WASM SQLite) so there is NO native compilation step —
 * works on any platform the Electron runtime targets. The database lives
 * in memory while running and is persisted to a file in userData on every
 * write (debounced) for durability across restarts.
 */
const fs = require("fs");
const path = require("path");

const LOCAL_SCHEMA = `
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
    line_items TEXT,
    issued_date TEXT,
    version INTEGER DEFAULT 1,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    method TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    payload TEXT,
    client_timestamp TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
    device_id TEXT PRIMARY KEY,
    last_pull_cursor TEXT,
    last_push_sequence INTEGER DEFAULT 0,
    last_sync_at TEXT
);
`;

let SQL = null;      // sql.js module
let db = null;       // Database instance
let dbFilePath = ""; // on-disk persistence path
let saveTimer = null;
let seqCounter = 0;

/** Resolve the sql.js wasm loader from the hoisted node_modules. */
function loadSqlJs() {
  // eslint-disable-next-line global-require
  const initSqlJs = require("sql.js");
  const wasmDir = path.dirname(require.resolve("sql.js/dist/sql-wasm.js"));
  return initSqlJs({ locateFile: (file) => path.join(wasmDir, file) });
}

/** Persist the in-memory DB to disk (debounced). */
function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try {
      const data = db.export();
      fs.writeFileSync(dbFilePath, Buffer.from(data));
    } catch (err) {
      console.error("[DB] Failed to persist:", err.message);
    }
  }, 300);
}

/** Initialize the local database. Loads existing file if present. */
async function initLocalDatabase(userDataDir) {
  SQL = await loadSqlJs();
  dbFilePath = path.join(userDataDir, "healthcare-os.db");

  if (fs.existsSync(dbFilePath)) {
    const fileBuffer = fs.readFileSync(dbFilePath);
    db = new SQL.Database(fileBuffer);
  } else {
    db = new SQL.Database();
  }
  db.run(LOCAL_SCHEMA);

  // Restore the sequence counter from the queue high-water mark.
  const row = db.exec("SELECT MAX(sequence_number) AS m FROM sync_queue");
  if (row.length && row[0].values[0][0] != null) {
    seqCounter = row[0].values[0][0];
  }
  scheduleSave();
  console.log("[DB] Local SQLite ready at", dbFilePath);
}

/** Run a read query, returning array of row objects. */
function query(sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const rows = [];
  while (stmt.step()) rows.push(stmt.getAsObject());
  stmt.free();
  return rows;
}

/** Run a write statement. */
function run(sql, params = []) {
  db.run(sql, params);
  scheduleSave();
}

/**
 * Enqueue a mutation for later sync. Called when the renderer is offline.
 * Returns the queue row id.
 */
function enqueueMutation({ entityType, entityId, operationType, method, endpoint, payload, idempotencyKey }) {
  seqCounter += 1;
  const id = `q_${Date.now()}_${seqCounter}`;
  const now = new Date().toISOString();
  db.run(
    `INSERT INTO sync_queue
       (id, entity_type, entity_id, operation_type, method, endpoint, payload,
        client_timestamp, sequence_number, status, retry_count, idempotency_key, created_at)
     VALUES (?,?,?,?,?,?,?,?,?, 'pending', 0, ?, ?)`,
    [
      id,
      entityType || "unknown",
      entityId || "",
      operationType || "create",
      method,
      endpoint,
      JSON.stringify(payload ?? null),
      now,
      seqCounter,
      idempotencyKey || id,
      now,
    ],
  );
  scheduleSave();
  return { id, sequence_number: seqCounter };
}

/** Get all pending queue items in order. */
function getPendingMutations() {
  return query(
    "SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY sequence_number ASC",
  );
}

/** Mark a queue item as synced (removes it) or failed. */
function resolveMutation(id, ok, errorMsg) {
  if (ok) {
    db.run("DELETE FROM sync_queue WHERE id = ?", [id]);
  } else {
    db.run(
      "UPDATE sync_queue SET status = 'pending', retry_count = retry_count + 1, last_error = ? WHERE id = ?",
      [errorMsg || "unknown", id],
    );
  }
  scheduleSave();
}

/** Count of pending mutations (drives the offline indicator badge). */
function pendingCount() {
  const rows = query("SELECT COUNT(*) AS c FROM sync_queue WHERE status = 'pending'");
  return rows.length ? rows[0].c : 0;
}

function close() {
  if (saveTimer) clearTimeout(saveTimer);
  if (db) {
    try {
      fs.writeFileSync(dbFilePath, Buffer.from(db.export()));
    } catch (err) {
      console.error("[DB] Final persist failed:", err.message);
    }
    db.close();
  }
}

module.exports = {
  LOCAL_SCHEMA,
  initLocalDatabase,
  query,
  run,
  enqueueMutation,
  getPendingMutations,
  resolveMutation,
  pendingCount,
  close,
};
