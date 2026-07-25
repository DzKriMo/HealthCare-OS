"use client";

import { useEffect, useState, useCallback } from "react";
import { getElectronBridge } from "@/lib/electron/bridge";
import type { SyncStatus } from "@/lib/electron/bridge";
import { api } from "@/lib/api/client";

/**
 * Tracks online/offline status and pending mutation count.
 * - In Electron: uses navigator.onLine + reports to main process + listens for
 *   sync:status-changed IPC events.
 * - In browser: uses navigator.onLine only; pending is always 0.
 */
export function useNetworkStatus() {
  const [status, setStatus] = useState<SyncStatus>({
    online: typeof navigator !== "undefined" ? navigator.onLine : true,
    pending: 0,
  });

  const report = useCallback((online: boolean) => {
    const bridge = getElectronBridge();
    bridge?.reportNetStatus(online);
  }, []);

  useEffect(() => {
    // Seed pending count from Electron on mount.
    const bridge = getElectronBridge();
    if (bridge) {
      bridge.getSyncStatus().then(setStatus).catch(() => {});
      bridge.onSyncStatusChange(setStatus);
    }

    const handleOnline = () => {
      setStatus((s) => ({ ...s, online: true }));
      report(true);
      // Replay any queued offline mutations, then refresh the badge.
      api.flushQueue()
        .then(() => getElectronBridge()?.getSyncStatus())
        .then((s) => s && setStatus(s))
        .catch(() => {});
    };
    const handleOffline = () => {
      setStatus((s) => ({ ...s, online: false }));
      report(false);
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [report]);

  return status;
}
