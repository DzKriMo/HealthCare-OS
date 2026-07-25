/**
 * Typed bridge to the Electron preload API (window.healthcareOS).
 * When running in a browser (no Electron), all methods are no-ops or stubs.
 */

export interface QueuedMutation {
  entityType: string;
  entityId: string;
  operationType: "create" | "update" | "delete";
  method: string;
  endpoint: string;
  payload?: unknown;
  idempotencyKey?: string;
}

export interface SyncStatus {
  online: boolean;
  pending: number;
}

interface HealthcareOSBridge {
  platform: string;
  version: string;
  serverUrl: string;
  // DB
  dbQuery: (sql: string, params?: unknown[]) => Promise<Record<string, unknown>[]>;
  dbRun: (sql: string, params?: unknown[]) => Promise<{ ok: boolean }>;
  // Queue
  enqueueMutation: (m: QueuedMutation) => Promise<{ id: string; sequence_number: number }>;
  getPendingMutations: () => Promise<Record<string, unknown>[]>;
  resolveMutation: (id: string, ok: boolean, err?: string) => Promise<{ ok: boolean }>;
  pendingCount: () => Promise<number>;
  // Connectivity
  reportNetStatus: (online: boolean) => void;
  getSyncStatus: () => Promise<SyncStatus>;
  onSyncStatusChange: (cb: (status: SyncStatus) => void) => void;
  // Window
  minimize: () => void;
  maximize: () => void;
  close: () => void;
  // File
  saveFile: (opts: { defaultPath?: string; filters?: unknown[]; contents?: string; encoding?: string }) => Promise<{ canceled: boolean; filePath?: string }>;
  openFile: (opts: { filters?: unknown[] }) => Promise<{ canceled: boolean; filePath?: string }>;
  // Print / notify / update
  print: () => Promise<{ ok: boolean }>;
  notify: (title: string, body: string) => void;
  checkForUpdates: () => Promise<{ updateAvailable: boolean }>;
  onUpdateAvailable: (cb: (info: unknown) => void) => void;
}

declare global {
  interface Window {
    healthcareOS?: HealthcareOSBridge;
  }
}

/** Returns the Electron bridge if running inside Electron, otherwise null. */
export function getElectronBridge(): HealthcareOSBridge | null {
  if (typeof window !== "undefined" && window.healthcareOS) {
    return window.healthcareOS;
  }
  return null;
}

/** True when running inside the Electron desktop app. */
export function isElectron(): boolean {
  return getElectronBridge() !== null;
}

/**
 * Enqueue a mutation for offline sync. Returns the queue entry id,
 * or null when not running in Electron (browser always goes online).
 */
export async function enqueueMutation(m: QueuedMutation): Promise<string | null> {
  const bridge = getElectronBridge();
  if (!bridge) return null;
  const res = await bridge.enqueueMutation(m);
  return res.id;
}
