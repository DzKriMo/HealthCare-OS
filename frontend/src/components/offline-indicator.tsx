"use client";

import { useNetworkStatus } from "@/hooks/use-network-status";

/**
 * Compact online/offline + pending-sync badge.
 * Renders nothing when online with no pending mutations.
 */
export function OfflineIndicator() {
  const { online, pending } = useNetworkStatus();

  if (online && pending === 0) return null;

  return (
    <div
      className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
        online
          ? "bg-yellow-100 text-yellow-800"
          : "bg-red-100 text-red-800"
      }`}
    >
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          online ? "bg-yellow-500" : "bg-red-500 animate-pulse"
        }`}
      />
      {online ? `Syncing (${pending})` : `Offline${pending > 0 ? ` · ${pending} queued` : ""}`}
    </div>
  );
}
