/**
 * Sync client — real implementation (P9.5).
 *
 * Runs in the Electron renderer process. Communicates with the main process
 * via the contextBridge API exposed in preload.js (window.healthcareOS).
 *
 * Push/pull cycle every 30s when online. Exponential backoff on failure.
 * Conflict strategy: server-wins (last-write-wins by server timestamp).
 */

declare global {
  interface Window {
    healthcareOS: {
      enqueueMutation: (m: SyncOperation) => Promise<void>;
      getPendingMutations: () => Promise<SyncOperation[]>;
      resolveMutation: (id: string, ok: boolean, err?: string) => Promise<void>;
      pendingCount: () => Promise<number>;
      dbQuery: (sql: string, params?: unknown[]) => Promise<unknown[]>;
      dbRun: (sql: string, params?: unknown[]) => Promise<void>;
      getSyncStatus: () => Promise<{ online: boolean; pendingCount: number }>;
      reportNetStatus: (online: boolean) => void;
    };
  }
}

export interface SyncOperation {
  id: string;
  entity_type: string;
  entity_id: string;
  operation_type: "create" | "update" | "delete";
  payload: Record<string, unknown>;
  base_version: number;
  client_timestamp: string;
  sequence_number: number;
  dependencies: string[];
  idempotency_key: string;
}

export interface SyncClientConfig {
  apiBaseUrl: string;
  tenantSlug: string;
  deviceId: string;
  authToken: string;
}

const SYNC_INTERVAL_MS = 30_000;
const MAX_BACKOFF_MS = 300_000; // 5 min cap

export class SyncClient {
  private config: SyncClientConfig;
  private isOnline: boolean = navigator.onLine;
  private syncInterval: ReturnType<typeof setInterval> | null = null;
  private sequenceCounter: number = 0;
  private failureCount: number = 0;

  constructor(config: SyncClientConfig) {
    this.config = config;
  }

  start(): void {
    window.addEventListener("online", () => this.onOnline());
    window.addEventListener("offline", () => this.onOffline());
    window.healthcareOS.reportNetStatus(this.isOnline);
    this.scheduleSyncLoop();
    console.log("[Sync] Background sync service started.");
  }

  stop(): void {
    if (this.syncInterval) clearInterval(this.syncInterval);
  }

  updateToken(token: string): void {
    this.config.authToken = token;
  }

  async enqueue(
    entityType: string,
    entityId: string,
    operationType: "create" | "update" | "delete",
    payload: Record<string, unknown>,
    baseVersion = 0,
  ): Promise<void> {
    this.sequenceCounter++;
    const op: SyncOperation = {
      id: crypto.randomUUID(),
      entity_type: entityType,
      entity_id: entityId,
      operation_type: operationType,
      payload,
      base_version: baseVersion,
      client_timestamp: new Date().toISOString(),
      sequence_number: this.sequenceCounter,
      dependencies: [],
      idempotency_key: crypto.randomUUID(),
    };
    await window.healthcareOS.enqueueMutation(op);
    console.log(`[Sync] Queued: ${operationType} ${entityType}#${entityId}`);
  }

  async sync(): Promise<void> {
    if (!this.isOnline) return;
    try {
      await this.push();
      await this.pull();
      this.failureCount = 0;
    } catch (err) {
      this.failureCount++;
      const backoff = Math.min(
        SYNC_INTERVAL_MS * Math.pow(2, this.failureCount - 1),
        MAX_BACKOFF_MS,
      );
      console.error(`[Sync] Failed (attempt ${this.failureCount}), retry in ${backoff}ms:`, err);
      setTimeout(() => this.sync(), backoff);
    }
  }

  private async push(): Promise<void> {
    const pending = await window.healthcareOS.getPendingMutations();
    if (pending.length === 0) return;

    const response = await fetch(`${this.config.apiBaseUrl}/sync/push/`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ device_id: this.config.deviceId, operations: pending }),
    });

    if (!response.ok) throw new Error(`Push failed: ${response.status}`);
    const result = await response.json();

    for (const op of result.accepted ?? []) {
      await window.healthcareOS.resolveMutation(op.idempotency_key, true);
    }
    for (const conflict of result.conflicted ?? []) {
      await this.handleConflict(conflict);
    }

    console.log(
      `[Sync] Push: ${result.accepted?.length ?? 0} accepted, ${result.conflicted?.length ?? 0} conflicts`,
    );
  }

  private async pull(): Promise<void> {
    const cursor = await this.getLastCursor();
    const response = await fetch(`${this.config.apiBaseUrl}/sync/pull/`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ device_id: this.config.deviceId, since_cursor: cursor }),
    });

    if (!response.ok) throw new Error(`Pull failed: ${response.status}`);
    const result = await response.json();

    if (result.changes?.length) {
      await this.applyRemoteChanges(result.changes);
      await this.updateCursor(result.cursor);
      console.log(`[Sync] Pull: ${result.changes.length} changes applied`);
    }
  }

  private async handleConflict(conflict: {
    idempotency_key: string;
    resolution: string;
    server_data?: Record<string, unknown>;
    entity_type?: string;
    entity_id?: string;
  }): Promise<void> {
    // Server-wins: mark local op as resolved, apply server data if provided.
    await window.healthcareOS.resolveMutation(conflict.idempotency_key, false, "conflict");
    if (conflict.server_data && conflict.entity_type && conflict.entity_id) {
      await this.upsertLocal(conflict.entity_type, conflict.entity_id, conflict.server_data);
    }
  }

  private async applyRemoteChanges(
    changes: Array<{ entity_type: string; entity_id: string; data: Record<string, unknown>; deleted?: boolean }>,
  ): Promise<void> {
    for (const change of changes) {
      if (change.deleted) {
        await window.healthcareOS.dbRun(
          `DELETE FROM ${change.entity_type}s WHERE id = ?`,
          [change.entity_id],
        );
      } else {
        await this.upsertLocal(change.entity_type, change.entity_id, change.data);
      }
    }
  }

  private async upsertLocal(
    entityType: string,
    entityId: string,
    data: Record<string, unknown>,
  ): Promise<void> {
    const table = `${entityType}s`;
    const cols = Object.keys(data);
    if (!cols.includes("id")) { cols.unshift("id"); data = { id: entityId, ...data }; }
    const placeholders = cols.map(() => "?").join(", ");
    const updates = cols.filter(c => c !== "id").map(c => `${c} = excluded.${c}`).join(", ");
    const sql = `INSERT INTO ${table} (${cols.join(", ")}) VALUES (${placeholders})
                 ON CONFLICT(id) DO UPDATE SET ${updates}`;
    await window.healthcareOS.dbRun(sql, cols.map(c => data[c]));
  }

  private async getLastCursor(): Promise<string> {
    const rows = await window.healthcareOS.dbQuery(
      "SELECT last_pull_cursor FROM sync_state WHERE device_id = ?",
      [this.config.deviceId],
    ) as Array<{ last_pull_cursor: string }>;
    return rows[0]?.last_pull_cursor ?? "";
  }

  private async updateCursor(cursor: string): Promise<void> {
    await window.healthcareOS.dbRun(
      `INSERT INTO sync_state (device_id, last_pull_cursor, last_sync_at)
       VALUES (?, ?, ?)
       ON CONFLICT(device_id) DO UPDATE SET last_pull_cursor = excluded.last_pull_cursor,
       last_sync_at = excluded.last_sync_at`,
      [this.config.deviceId, cursor, new Date().toISOString()],
    );
  }

  private headers(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${this.config.authToken}`,
      "X-Tenant-Slug": this.config.tenantSlug,
    };
  }

  private scheduleSyncLoop(): void {
    this.syncInterval = setInterval(() => this.sync(), SYNC_INTERVAL_MS);
    // Immediate first sync
    this.sync();
  }

  private onOnline(): void {
    this.isOnline = true;
    window.healthcareOS.reportNetStatus(true);
    console.log("[Sync] Online — syncing now.");
    this.sync();
  }

  private onOffline(): void {
    this.isOnline = false;
    window.healthcareOS.reportNetStatus(false);
    console.log("[Sync] Offline — mutations will queue locally.");
  }
}
