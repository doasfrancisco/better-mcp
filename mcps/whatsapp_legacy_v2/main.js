/**
 * WhatsApp Electron — WhatsApp Web wrapper with built-in MCP server.
 *
 * Opening this app = MCP server is live on port 39571.
 * No separate server process, no hooks, no Puppeteer.
 */

import { app, BrowserWindow, shell, screen, ipcMain, session } from "electron";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import { startMcpServer, setBridge } from "./mcp-server.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STATE_FILE = path.join(app.getPath("userData"), "window-state.json");
const WHATSAPP_URL = "https://web.whatsapp.com";

// ── Window state persistence ──────────────────────────────────

function loadWindowState() {
  try {
    if (!fs.existsSync(STATE_FILE)) return getCenteredState(1200, 800);
    const state = JSON.parse(fs.readFileSync(STATE_FILE, "utf-8"));
    if (!state.width || !state.height || isNaN(state.x) || isNaN(state.y)) {
      return getCenteredState(1200, 800);
    }
    const displays = screen.getAllDisplays();
    const display = displays.find((d) => d.id === state.displayId);
    if (!display) return getCenteredState(state.width, state.height);
    const b = display.bounds;
    if (state.x < b.x || state.y < b.y || state.x + state.width > b.x + b.width || state.y + state.height > b.y + b.height) {
      return getCenteredState(state.width, state.height, b);
    }
    return state;
  } catch {
    return getCenteredState(1200, 800);
  }
}

function saveWindowState(win) {
  if (win.isMinimized() || win.isFullScreen()) return;
  try {
    const bounds = win.getBounds();
    const display = screen.getDisplayMatching(bounds);
    fs.writeFileSync(STATE_FILE, JSON.stringify({ ...bounds, displayId: display.id }));
  } catch {}
}

function getCenteredState(width, height, bounds = screen.getPrimaryDisplay().bounds) {
  return {
    width,
    height,
    x: Math.max(bounds.x, Math.floor(bounds.x + (bounds.width - width) / 2)),
    y: Math.max(bounds.y, Math.floor(bounds.y + (bounds.height - height) / 2)),
    displayId: screen.getPrimaryDisplay().id,
  };
}

// ── Context menu ──────────────────────────────────────────────

import("electron-context-menu").then((m) => m.default({ showSaveImageAs: true }));

// ── App state ─────────────────────────────────────────────────

let win = null;
let waReady = false; // true once WhatsApp Store is injected and accessible

// State accessors (used by setBridge to wire MCP server → renderer)

// ── IPC handlers ──────────────────────────────────────────────

ipcMain.handle("wa:ready", () => {
  waReady = true;
  console.error("[whatsapp-electron] WhatsApp Store ready");
});

ipcMain.handle("wa:state", () => waReady);

// ── Inject Store bridge after WhatsApp Web loads ──────────────

async function injectBridge() {
  if (!win) return;
  const injectCode = fs.readFileSync(path.join(__dirname, "inject.js"), "utf-8");
  try {
    await win.webContents.executeJavaScript(injectCode);
    console.error("[whatsapp-electron] inject.js executed");
  } catch (err) {
    console.error("[whatsapp-electron] inject.js failed:", err.message);
  }
}

// Poll for Store readiness after injection
async function waitForStore() {
  const maxAttempts = 60; // 60s
  for (let i = 0; i < maxAttempts; i++) {
    if (waReady) return true;
    try {
      const ready = await win.webContents.executeJavaScript("typeof window.__waAPI !== 'undefined' && window.__waAPI._ready === true");
      if (ready) {
        waReady = true;
        console.error("[whatsapp-electron] WhatsApp Store confirmed ready");
        return true;
      }
    } catch {}
    await new Promise((r) => setTimeout(r, 1000));
  }
  console.error("[whatsapp-electron] WhatsApp Store not ready after 60s");
  return false;
}

// ── Create window ─────────────────────────────────────────────

function createWindow() {
  const windowState = loadWindowState();

  // User agent — match real Chrome to avoid WhatsApp's "unsupported browser" block
  const chromeVersion = process.versions.chrome;
  const userAgent = `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${chromeVersion} Safari/537.36`;

  win = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    x: windowState.x,
    y: windowState.y,
    icon: path.join(__dirname, "icon.png"),
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false, // needed for preload to use Node APIs for IPC
    },
  });

  // Strip CSP headers so our injected scripts can run
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const headers = { ...details.responseHeaders };
    delete headers["content-security-policy"];
    delete headers["Content-Security-Policy"];
    callback({ responseHeaders: headers });
  });

  win.loadURL(WHATSAPP_URL, { userAgent });

  // Open external links in default browser
  win.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: "deny" };
  });

  win.on("close", () => saveWindowState(win));

  // Inject our bridge once WhatsApp Web finishes loading
  win.webContents.on("did-finish-load", async () => {
    console.error("[whatsapp-electron] Page loaded, injecting bridge...");
    // Wait a bit for WhatsApp's JS to initialize webpack
    await new Promise((r) => setTimeout(r, 3000));
    await injectBridge();
    waitForStore(); // runs in background, sets waReady
  });

  // Re-inject on navigation (WhatsApp Web sometimes reloads)
  win.webContents.on("did-navigate-in-page", async () => {
    if (!waReady) return;
    waReady = false;
    await new Promise((r) => setTimeout(r, 2000));
    await injectBridge();
    waitForStore();
  });
}

// ── Single instance lock ──────────────────────────────────────

const appLock = app.requestSingleInstanceLock();
if (!appLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (win) {
      if (win.isMinimized()) win.restore();
      win.focus();
    }
  });

  app.on("ready", async () => {
    createWindow();

    // Wire up the bridge so MCP server can call into the renderer
    setBridge(() => win, () => waReady);

    // Start MCP server — Claude Code connects here
    try {
      await startMcpServer();
      console.error("[whatsapp-electron] MCP server started on port 39571");
    } catch (err) {
      console.error("[whatsapp-electron] MCP server failed to start:", err.message);
    }
  });
}

// ── Protocol handler ──────────────────────────────────────────

const protocolClient = "whatsapp";
if (!app.isDefaultProtocolClient(protocolClient, process.execPath)) {
  app.setAsDefaultProtocolClient(protocolClient, process.execPath);
}
