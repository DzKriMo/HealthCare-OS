"use client";

import { useEffect, useState } from "react";

/**
 * Offline indicator (P7.4).
 *
 * Shows a fixed banner when the browser loses connectivity. In the Electron
 * shell it also reports status to the main process so the sync client and
 * tray icon can react.
 */
export function OfflineIndicator() {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    setOnline(navigator.onLine);

    const update = () => {
      const isOnline = navigator.onLine;
      setOnline(isOnline);
      // Report to Electron main process if present
      const bridge = (window as unknown as {
        healthcareOS?: { reportNetStatus?: (v: boolean) => void };
      }).healthcareOS;
      bridge?.reportNetStatus?.(isOnline);
    };

    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (online) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 top-0 z-50 flex items-center justify-center gap-2 bg-amber-500 px-4 py-2 text-sm font-medium text-amber-950 shadow"
    >
      <span className="h-2 w-2 rounded-full bg-amber-950" aria-hidden />
      You are offline. Changes are saved locally and will sync when reconnected.
    </div>
  );
}
