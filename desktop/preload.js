/**
 * Preload script — secure bridge between Electron main process and renderer.
 *
 * Exposes limited, safe APIs to the renderer via contextBridge.
 * The renderer (Next.js app) cannot access Node.js or Electron APIs directly.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("healthcareOS", {
  // ── App Info ───────────────────────────────────────────
  platform: process.platform,
  version: process.env.npm_package_version || "1.0.0",
  serverUrl: process.env.HEALTHCARE_OS_URL || "http://localhost:3000",

  // ── Window Controls ────────────────────────────────────
  minimize: () => ipcRenderer.send("window:minimize"),
  maximize: () => ipcRenderer.send("window:maximize"),
  close: () => ipcRenderer.send("window:close"),

  // ── Local database (read/write mirror) ─────────────────
  dbQuery: (sql, params) => ipcRenderer.invoke("db:query", sql, params),
  dbRun: (sql, params) => ipcRenderer.invoke("db:run", sql, params),

  // ── Offline mutation queue ─────────────────────────────
  enqueueMutation: (mutation) => ipcRenderer.invoke("queue:enqueue", mutation),
  getPendingMutations: () => ipcRenderer.invoke("queue:pending"),
  resolveMutation: (id, ok, err) => ipcRenderer.invoke("queue:resolve", id, ok, err),
  pendingCount: () => ipcRenderer.invoke("queue:count"),

  // ── Connectivity (renderer → main) ─────────────────────
  reportNetStatus: (online) => ipcRenderer.send("net:status", online),

  // ── Sync Status ────────────────────────────────────────
  getSyncStatus: () => ipcRenderer.invoke("sync:status"),
  onSyncStatusChange: (callback) => {
    ipcRenderer.on("sync:status-changed", (_, status) => callback(status));
  },

  // ── File System (limited) ──────────────────────────────
  saveFile: (options) => ipcRenderer.invoke("file:save", options),
  openFile: (options) => ipcRenderer.invoke("file:open", options),

  // ── Printing ───────────────────────────────────────────
  print: (options) => ipcRenderer.invoke("print", options),

  // ── Notifications ──────────────────────────────────────
  notify: (title, body) => ipcRenderer.send("notification:show", { title, body }),

  // ── Updates ────────────────────────────────────────────
  checkForUpdates: () => ipcRenderer.invoke("update:check"),
  onUpdateAvailable: (callback) => {
    ipcRenderer.on("update:available", (_, info) => callback(info));
  },
});

// Log that preload completed successfully
console.log("[Healthcare OS] Preload script loaded. Server:", process.env.HEALTHCARE_OS_URL || "http://localhost:3000");
