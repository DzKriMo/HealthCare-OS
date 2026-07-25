const { app, BrowserWindow, Tray, Menu, nativeImage, globalShortcut, dialog, shell, ipcMain, Notification } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const db = require("./database");

let mainWindow = null;
let tray = null;
let isQuitting = false;
let isOnline = true;
let serverProcess = null;

const isDev = process.argv.includes("--dev") || !app.isPackaged;
const SERVER_URL = process.env.HEALTHCARE_OS_URL || "http://localhost:3000";
const FRONTEND_DIR = isDev ? null : path.join(process.resourcesPath, "frontend");
const LICENSE_FILE = "healthcare-os.lic";

function getLicensePath() {
  return path.join(app.getPath("userData"), LICENSE_FILE);
}

function checkLicense() {
  const licPath = getLicensePath();
  if (fs.existsSync(licPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(licPath, "utf8"));
      if (data.licenseKey && data.email) return { valid: true, ...data };
    } catch { }
  }
  return { valid: false };
}

function saveLicense(key, email) {
  fs.writeFileSync(getLicensePath(), JSON.stringify({ licenseKey: key, email, activatedAt: new Date().toISOString() }, null, 2));
}

function startServer() {
  if (isDev) return;
  const nextPath = path.join(FRONTEND_DIR, "node_modules", ".bin", process.platform === "win32" ? "next.cmd" : "next");
  const cwd = FRONTEND_DIR;
  if (!fs.existsSync(path.join(cwd, "package.json"))) {
    console.warn("[Server] frontend not bundled — skipping server start");
    return;
  }
  serverProcess = spawn(nextPath, ["start", "-p", "3000"], { cwd, stdio: "pipe" });
  serverProcess.stdout?.on("data", (d) => process.stdout.write(`[Next] ${d}`));
  serverProcess.stderr?.on("data", (d) => process.stderr.write(`[Next] ${d}`));
  serverProcess.on("exit", (code) => console.log(`[Server] exited code ${code}`));
}

function stopServer() {
  if (serverProcess) {
    serverProcess.kill();
    serverProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900, minWidth: 1024, minHeight: 700,
    title: "Healthcare OS",
    icon: path.join(__dirname, "assets", "icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    show: false,
  });

  mainWindow.loadURL(SERVER_URL);
  mainWindow.once("ready-to-show", () => mainWindow.show());

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.on("close", (event) => {
    if (!isQuitting) { event.preventDefault(); mainWindow.hide(); }
  });
  mainWindow.on("closed", () => { mainWindow = null; });
}

function buildAppMenu() {
  const lic = checkLicense();
  const licenseLabel = lic.valid ? `License: ${lic.email}` : "Activate License";
  const template = [
    {
      label: "File",
      submenu: [
        {
          label: "Backup Database",
          click: async () => {
            const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
              defaultPath: `healthcare-os-backup-${new Date().toISOString().slice(0, 10)}.db`,
              filters: [{ name: "SQLite Database", extensions: ["db"] }],
            });
            if (!canceled && filePath) {
              try {
                const data = db.export();
                fs.writeFileSync(filePath, Buffer.from(data));
                dialog.showMessageBox(mainWindow, { type: "info", message: "Backup saved successfully.", title: "Healthcare OS" });
              } catch (err) { dialog.showErrorBox("Backup Failed", err.message); }
            }
          },
        },
        {
          label: "Restore Database",
          click: async () => {
            const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
              filters: [{ name: "SQLite Database", extensions: ["db"] }],
              properties: ["openFile"],
            });
            if (!canceled && filePaths.length) {
              const choice = dialog.showMessageBoxSync(mainWindow, {
                type: "warning", buttons: ["Cancel", "Restore"],
                message: "Restore will replace all local data. Continue?",
                title: "Healthcare OS",
              });
              if (choice === 1) {
                try {
                  const buf = fs.readFileSync(filePaths[0]);
                  db.restore(buf);
                  dialog.showMessageBox(mainWindow, { type: "info", message: "Database restored. Restart the app.", title: "Healthcare OS" });
                } catch (err) { dialog.showErrorBox("Restore Failed", err.message); }
              }
            }
          },
        },
        { type: "separator" },
        {
          label: licenseLabel,
          click: () => {
            if (!lic.valid) showLicenseDialog();
            else dialog.showMessageBox(mainWindow, { type: "info", message: `Activated to ${lic.email}`, title: "License" });
          },
        },
        { type: "separator" },
        { role: "quit", label: "Exit Healthcare OS" },
      ],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "About Healthcare OS",
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: "info", title: "About Healthcare OS",
              message: "Healthcare OS — Desktop Edition",
              detail: `Version ${app.getVersion()}\n\nOffline-first healthcare management platform.\n\n© ${new Date().getFullYear()} Healthcare OS`,
            });
          },
        },
        { type: "separator" },
        { role: "toggleDevTools", label: "Developer Tools" },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function showLicenseDialog() {
  dialog.showMessageBox(mainWindow, {
    type: "info", title: "Activate License",
    message: "Healthcare OS License",
    detail: "Enter your license key in the app settings.\n\nTo purchase a license, visit healthcare-os.com",
  });
}

function createTray() {
  const iconPath = path.join(__dirname, "assets", "icon.png");
  let trayIcon;
  try { trayIcon = nativeImage.createFromPath(iconPath).resize({ width: 16, height: 16 }); }
  catch { trayIcon = nativeImage.createEmpty(); }
  tray = new Tray(trayIcon);
  tray.setToolTip("Healthcare OS");
  updateTrayLabel();
  tray.on("double-click", () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } });
}

function updateTrayLabel() {
  if (!tray) return;
  const pending = safePendingCount();
  const label = isOnline
    ? pending > 0 ? `Syncing (${pending})` : "Online"
    : `Offline (${pending} queued)`;
  const template = [
    { label: "Open Healthcare OS", click: () => { if (mainWindow) { mainWindow.show(); mainWindow.focus(); } else createWindow(); } },
    { type: "separator" },
    { label: `Status: ${label}`, enabled: false },
    { type: "separator" },
    { label: "Check for Updates", click: () => dialog.showMessageBox({ message: "You are running the latest version.", title: "Healthcare OS" }) },
    { type: "separator" },
    { label: "Quit", click: () => { isQuitting = true; app.quit(); } },
  ];
  tray.setContextMenu(Menu.buildFromTemplate(template));
}

function safePendingCount() {
  try { return db.pendingCount(); } catch { return 0; }
}

function registerShortcuts() {
  globalShortcut.register("CommandOrControl+Shift+P", () => {
    if (mainWindow) { mainWindow.show(); mainWindow.focus(); mainWindow.webContents.executeJavaScript(`document.querySelector('input[placeholder*="Search"]')?.focus()`); }
  });
  globalShortcut.register("CommandOrControl+Shift+N", () => {
    if (mainWindow) { mainWindow.show(); mainWindow.focus(); mainWindow.webContents.executeJavaScript(`window.location.href = '/appointments/new'`); }
  });
  globalShortcut.register("CommandOrControl+Shift+I", () => {
    if (mainWindow) mainWindow.webContents.toggleDevTools();
  });
}

function registerIpc() {
  ipcMain.handle("db:query", (_e, sql, params) => db.query(sql, params));
  ipcMain.handle("db:run", (_e, sql, params) => { db.run(sql, params); return { ok: true }; });
  ipcMain.handle("queue:enqueue", (_e, mutation) => { const res = db.enqueueMutation(mutation); updateTrayLabel(); broadcastSyncStatus(); return res; });
  ipcMain.handle("queue:pending", () => db.getPendingMutations());
  ipcMain.handle("queue:resolve", (_e, id, ok, err) => { db.resolveMutation(id, ok, err); updateTrayLabel(); broadcastSyncStatus(); return { ok: true }; });
  ipcMain.handle("queue:count", () => safePendingCount());
  ipcMain.on("net:status", (_e, online) => { isOnline = !!online; updateTrayLabel(); broadcastSyncStatus(); });
  ipcMain.handle("sync:status", () => ({ online: isOnline, pending: safePendingCount() }));
  ipcMain.handle("license:check", () => checkLicense());
  ipcMain.handle("license:activate", (_e, key, email) => { saveLicense(key, email); return { ok: true }; });
  ipcMain.handle("backup:create", async () => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, { defaultPath: `healthcare-os-backup-${new Date().toISOString().slice(0, 10)}.db`, filters: [{ name: "SQLite Database", extensions: ["db"] }] });
    if (canceled || !filePath) return { canceled: true };
    try { const data = db.export(); fs.writeFileSync(filePath, Buffer.from(data)); return { canceled: false, filePath }; }
    catch (err) { return { canceled: false, error: err.message }; }
  });
  ipcMain.handle("restore:execute", async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, { filters: [{ name: "SQLite Database", extensions: ["db"] }], properties: ["openFile"] });
    if (canceled || !filePaths.length) return { canceled: true };
    try { const buf = fs.readFileSync(filePaths[0]); db.restore(buf); return { canceled: false }; }
    catch (err) { return { canceled: false, error: err.message }; }
  });
  ipcMain.handle("file:save", async (_e, options = {}) => {
    const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, { defaultPath: options.defaultPath, filters: options.filters });
    if (canceled || !filePath) return { canceled: true };
    if (options.contents != null) {
      const buf = options.encoding === "base64" ? Buffer.from(options.contents, "base64") : Buffer.from(String(options.contents), "utf8");
      fs.writeFileSync(filePath, buf);
    }
    return { canceled: false, filePath };
  });
  ipcMain.handle("file:open", async (_e, options = {}) => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, { properties: ["openFile"], filters: options.filters });
    if (canceled || !filePaths.length) return { canceled: true };
    return { canceled: false, filePath: filePaths[0] };
  });
  ipcMain.handle("print", async () => {
    if (!mainWindow) return { ok: false };
    return new Promise((resolve) => { mainWindow.webContents.print({ silent: false }, (success) => resolve({ ok: success })); });
  });
  ipcMain.on("notification:show", (_e, { title, body }) => { if (Notification.isSupported()) new Notification({ title: title || "Healthcare OS", body: body || "" }).show(); });
  ipcMain.handle("update:check", () => ({ updateAvailable: false }));
  ipcMain.on("window:minimize", () => mainWindow && mainWindow.minimize());
  ipcMain.on("window:maximize", () => { if (!mainWindow) return; mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize(); });
  ipcMain.on("window:close", () => mainWindow && mainWindow.hide());
}

function broadcastSyncStatus() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("sync:status-changed", { online: isOnline, pending: safePendingCount() });
  }
}

app.whenReady().then(async () => {
  try { await db.initLocalDatabase(app.getPath("userData")); }
  catch (err) { console.error("[DB] init failed:", err); }
  buildAppMenu();
  registerIpc();
  if (!isDev) startServer();
  createWindow();
  createTray();
  registerShortcuts();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); else if (mainWindow) mainWindow.show(); });
});

app.on("before-quit", () => { isQuitting = true; });

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
  stopServer();
  try { db.close(); } catch (err) { console.error("[DB] close failed:", err.message); }
});

app.on("window-all-closed", () => { });
