/**
 * Healthcare OS — Electron Desktop Application
 *
 * Main process: window management, tray, auto-updater,
 * SQLite local database, sync background service.
 */

import { app, BrowserWindow, Tray, Menu, nativeImage, globalShortcut } from "electron";
import path from "path";

// Will be implemented in Sprint 9 full build
// For now: scaffold structure

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "Healthcare OS",
    icon: path.join(__dirname, "../../assets/icon.png"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  // Load the Next.js web app (in production: bundled)
  const isDev = process.env.NODE_ENV === "development";
  if (isDev) {
    mainWindow.loadURL("http://localhost:3000");
  } else {
    mainWindow.loadFile(path.join(__dirname, "../../dist/renderer/index.html"));
  }

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function createTray(): void {
  // Tray icon for background sync status
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);
  tray.setToolTip("Healthcare OS");

  const contextMenu = Menu.buildFromTemplate([
    { label: "Open Healthcare OS", click: () => mainWindow?.show() },
    { label: "Sync Status: Connected", enabled: false },
    { type: "separator" },
    { label: "Quit", click: () => app.quit() },
  ]);
  tray.setContextMenu(contextMenu);
}

function registerShortcuts(): void {
  // Global shortcuts for quick actions
  globalShortcut.register("CommandOrControl+Shift+P", () => {
    mainWindow?.webContents.send("shortcut:patient-search");
  });
  globalShortcut.register("CommandOrControl+Shift+N", () => {
    mainWindow?.webContents.send("shortcut:new-appointment");
  });
}

// Auto-updater (in production)
// import { autoUpdater } from "electron-updater";
// autoUpdater.checkForUpdatesAndNotify();

app.whenReady().then(() => {
  createWindow();
  createTray();
  registerShortcuts();
});

app.on("window-all-closed", () => {
  // Keep running in tray for sync
  if (process.platform !== "darwin") {
    // app.quit(); — commented: keep sync running
  }
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});
