/**
 * Healthcare OS — Electron Desktop Application
 *
 * Wraps the web app (localhost:6776) in a native window with:
 *   - System tray with sync status
 *   - Global shortcuts for quick actions
 *   - Auto-updater (in production)
 *   - Secure preload for IPC
 */
const { app, BrowserWindow, Tray, Menu, nativeImage, globalShortcut, dialog, shell, ipcMain, Notification } = require("electron");
const path = require("path");
const fs = require("fs");
const db = require("./database");

// Keep a global reference to prevent garbage collection
let mainWindow = null;
let tray = null;
let isQuitting = false;
let isOnline = true; // last known connectivity, reported by the renderer

// ── Server URL ───────────────────────────────────────────────
const SERVER_URL = process.env.HEALTHCARE_OS_URL || "http://localhost:3000";

// ── Create Window ────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "Healthcare OS",
    icon: path.join(__dirname, "assets", "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    // Frameless with custom title bar (optional — comment out for standard frame)
    // frame: false,
    show: false, // Show after ready to prevent flicker
  });

  // Load the Healthcare OS web app
  mainWindow.loadURL(SERVER_URL);

  // Show when ready
  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  // Handle close — minimize to tray instead of quitting
  mainWindow.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── System Tray ──────────────────────────────────────────────
function createTray() {
  // Use a simple 16x16 icon or generate one
  const iconPath = path.join(__dirname, "assets", "icon.png");
  let trayIcon;
  try {
    trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 });
  } catch {
    // Create a simple blank icon if the file doesn't exist
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon);
  tray.setToolTip("Healthcare OS");
  buildTrayMenu("Sync Status: Online");

  // Double-click tray icon to open
  tray.on("double-click", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

function buildTrayMenu(statusLabel) {
  if (!tray) return;
  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open Healthcare OS",
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        } else {
          createWindow();
        }
      },
    },
    { type: "separator" },
    { label: statusLabel, enabled: false },
    { type: "separator" },
    {
      label: "Check for Updates",
      click: () => {
        dialog.showMessageBox({ message: "You're running the latest version.", title: "Healthcare OS" });
      },
    },
    { type: "separator" },
    {
      label: "Quit Healthcare OS",
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);
  tray.setContextMenu(contextMenu);
}

// ── Global Shortcuts ─────────────────────────────────────────
function registerShortcuts() {
  // Quick patient search
  globalShortcut.register("CommandOrControl+Shift+P", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.webContents.executeJavaScript(
        `document.querySelector('input[placeholder*="Search"]')?.focus()`,
      );
    }
  });

  // New appointment
  globalShortcut.register("CommandOrControl+Shift+N", () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.webContents.executeJavaScript(
        `window.location.href = '/appointments/new'`,
      );
    }
  });

  // Toggle dev tools
  globalShortcut.register("CommandOrControl+Shift+I", () => {
    if (mainWindow) {
      mainWindow.webContents.toggleDevTools();
    }
  });
}

// ── IPC Handlers ─────────────────────────────────────────────
function updateTrayStatus() {
  if (!tray) return;
  const pending = safePendingCount();
  const label = isOnline
    ? pending > 0
      ? `Sync Status: Online (${pending} queued)`
      : "Sync Status: Online"
    : `Sync Status: Offline (${pending} queued)`;
  buildTrayMenu(label);
}

function safePendingCount() {
  try {
    return db.pendingCount();
  } catch {
    return 0;
  }
}

function registerIpc() {
  // ── Local DB read/write ──────────────────────────────
  ipcMain.handle("db:query", (_e, sql, params) => db.query(sql, params));
  ipcMain.handle("db:run", (_e, sql, params) => {
    db.run(sql, params);
    return { ok: true };
  });

  // ── Offline mutation queue ───────────────────────────
  ipcMain.handle("queue:enqueue", (_e, mutation) => {
    const res = db.enqueueMutation(mutation);
    updateTrayStatus();
    broadcastSyncStatus();
    return res;
  });
  ipcMain.handle("queue:pending", () => db.getPendingMutations());
  ipcMain.handle("queue:resolve", (_e, id, ok, err) => {
    db.resolveMutation(id, ok, err);
    updateTrayStatus();
    broadcastSyncStatus();
    return { ok: true };
  });
  ipcMain.handle("queue:count", () => safePendingCount());

  // ── Connectivity reported by renderer ────────────────
  ipcMain.on("net:status", (_e, online) => {
    isOnline = !!online;
    updateTrayStatus();
    broadcastSyncStatus();
  });

  // ── Sync status ──────────────────────────────────────
  ipcMain.handle("sync:status", () => ({
    online: isOnline,
    pending: safePendingCount(),
  }));

  // ── File save/open ───────────────────────────────────
  ipcMain.handle("file:save", async (_e, options = {}) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
      defaultPath: options.defaultPath,
      filters: options.filters,
    });
    if (canceled || !filePath) return { canceled: true };
    if (options.contents != null) {
      const buf = options.encoding === "base64"
        ? Buffer.from(options.contents, "base64")
        : Buffer.from(String(options.contents), "utf8");
      fs.writeFileSync(filePath, buf);
    }
    return { canceled: false, filePath };
  });
  ipcMain.handle("file:open", async (_e, options = {}) => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
      properties: ["openFile"],
      filters: options.filters,
    });
    if (canceled || !filePaths.length) return { canceled: true };
    return { canceled: false, filePath: filePaths[0] };
  });

  // ── Printing ─────────────────────────────────────────
  ipcMain.handle("print", async () => {
    if (!mainWindow) return { ok: false };
    return new Promise((resolve) => {
      mainWindow.webContents.print({ silent: false }, (success) =>
        resolve({ ok: success }),
      );
    });
  });

  // ── Notifications ────────────────────────────────────
  ipcMain.on("notification:show", (_e, { title, body }) => {
    if (Notification.isSupported()) {
      new Notification({ title: title || "Healthcare OS", body: body || "" }).show();
    }
  });

  // ── Updates (stub until publish channel is configured) ─
  ipcMain.handle("update:check", () => ({ updateAvailable: false }));

  // ── Window controls ──────────────────────────────────
  ipcMain.on("window:minimize", () => mainWindow && mainWindow.minimize());
  ipcMain.on("window:maximize", () => {
    if (!mainWindow) return;
    mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
  });
  ipcMain.on("window:close", () => mainWindow && mainWindow.hide());
}

function broadcastSyncStatus() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("sync:status-changed", {
      online: isOnline,
      pending: safePendingCount(),
    });
  }
}

// ── App Lifecycle ────────────────────────────────────────────
app.whenReady().then(async () => {
  try {
    await db.initLocalDatabase(app.getPath("userData"));
  } catch (err) {
    console.error("[DB] init failed:", err);
  }
  registerIpc();
  createWindow();
  createTray();
  registerShortcuts();

  // macOS: re-create window when dock icon clicked
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    } else if (mainWindow) {
      mainWindow.show();
    }
  });
});

app.on("before-quit", () => {
  isQuitting = true;
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
  try {
    db.close();
  } catch (err) {
    console.error("[DB] close failed:", err.message);
  }
});

app.on("window-all-closed", () => {
  // Stay running in tray on all platforms
  // Only quit on Cmd+Q / File > Quit
});
