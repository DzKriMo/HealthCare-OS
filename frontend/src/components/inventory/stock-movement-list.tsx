"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";

interface StockMovement {
  id: string;
  item: string;
  item_name: string;
  batch: string;
  movement_type: string;
  quantity: number;
  quantity_before: number;
  quantity_after: number;
  reference_type: string;
  reference_id: string;
  reason: string;
  performed_by_name: string;
  created_at: string;
}

interface StockMovementListProps {
  itemId: string;
}

const TYPE_STYLES: Record<string, string> = {
  in: "bg-green-100 text-green-700",
  out: "bg-red-100 text-red-700",
  adjustment: "bg-blue-100 text-blue-700",
  waste: "bg-orange-100 text-orange-700",
  return: "bg-purple-100 text-purple-700",
};

export function StockMovementList({ itemId }: StockMovementListProps) {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!itemId) return;
    const load = async () => {
      try {
        setMovements(await api.get<StockMovement[]>(`/inventory/stock/movements/?item=${itemId}`));
      } catch { }
      setLoading(false);
    };
    load();
  }, [itemId]);

  if (!itemId) {
    return <div className="text-sm text-muted-foreground">Select an item to view stock movements.</div>;
  }

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading movements...</div>;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">Stock Movements ({movements.length})</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase text-muted-foreground">
              <th className="pb-2 pr-4 font-medium">Type</th>
              <th className="pb-2 pr-4 font-medium">Qty</th>
              <th className="pb-2 pr-4 font-medium">Before → After</th>
              <th className="pb-2 pr-4 font-medium">Reason</th>
              <th className="pb-2 pr-4 font-medium">By</th>
              <th className="pb-2 pr-4 font-medium">Date</th>
            </tr>
          </thead>
          <tbody>
            {movements.map((m) => (
              <tr key={m.id} className="border-b last:border-0">
                <td className="py-2 pr-4">
                  <span className={cn("inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium", TYPE_STYLES[m.movement_type] || "bg-gray-100 text-gray-700")}>
                    {m.movement_type}
                  </span>
                </td>
                <td className={cn("py-2 pr-4 font-mono font-medium", m.quantity < 0 ? "text-red-600" : "text-green-600")}>
                  {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                </td>
                <td className="py-2 pr-4 font-mono text-muted-foreground">
                  {m.quantity_before} → {m.quantity_after}
                </td>
                <td className="max-w-[200px] truncate py-2 pr-4 text-muted-foreground">
                  {m.reason || "—"}
                </td>
                <td className="py-2 pr-4 text-muted-foreground">
                  {m.performed_by_name || "—"}
                </td>
                <td className="py-2 pr-4 text-muted-foreground whitespace-nowrap">
                  {m.created_at ? new Date(m.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {movements.length === 0 && (
        <p className="text-sm text-muted-foreground">No movements recorded.</p>
      )}
    </div>
  );
}
