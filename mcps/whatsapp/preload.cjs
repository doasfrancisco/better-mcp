/**
 * Preload script — runs in a sandboxed context with access to ipcRenderer.
 * Exposes a minimal bridge so inject.js (running in page context) can
 * communicate back to the Electron main process via postMessage → IPC.
 *
 * CommonJS required because Electron loads preloads via require(),
 * regardless of package.json "type": "module".
 */

const { contextBridge, ipcRenderer } = require("electron");

// Expose a bridge the page context can call via window.__electronBridge
contextBridge.exposeInMainWorld("__electronBridge", {
  // Called by inject.js once Store modules are found and API is ready
  storeReady: () => ipcRenderer.invoke("wa:ready"),

  // Called by inject.js to send extracted data back to main process
  sendData: (channel, data) => ipcRenderer.invoke(`wa:data:${channel}`, data),
});

// Listen for requests from main process (MCP tool calls)
// The main process sends these, and inject.js picks them up via window events
ipcRenderer.on("wa:request", (_event, requestId, method, args) => {
  // Forward to page context via custom event on window
  window.dispatchEvent(
    new CustomEvent("__wa_request", {
      detail: { requestId, method, args },
    })
  );
});

// Page context sends responses back via postMessage
window.addEventListener("message", (event) => {
  if (event.data?.type === "__wa_response") {
    ipcRenderer.invoke("wa:response", event.data.requestId, event.data.result, event.data.error);
  }
});
