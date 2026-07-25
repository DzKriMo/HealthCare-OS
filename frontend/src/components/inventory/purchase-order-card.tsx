"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface PurchaseOrderLineItem {
  id: number;
  item: string;
  item_name: string;
  quantity: number;
  unit_cost: string;
  line_total: string;
}

interface PurchaseOrder {
  id: string;
  supplier: string;
  supplier_name: string;
  po_number: string;
  status: string;
  notes: string;
  line_items: PurchaseOrderLineItem[];
  total_cost: string;
  ordered_by_name: string;
  ordered_date: string;
  expected_date: string;
  received_date: string;
}

interface PurchaseOrderCardProps {
  order: PurchaseOrder;
  onClick: () => void;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  sent: "bg-blue-100 text-blue-700",
  partially_received: "bg-amber-100 text-amber-700",
  received: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
};

export function PurchaseOrderCard({ order, onClick }: PurchaseOrderCardProps) {
  const statusStyle = STATUS_STYLES[order.status] || "bg-gray-100 text-gray-700";

  return (
    <Card className="cursor-pointer transition-colors hover:border-primary" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate font-mono text-sm font-medium">{order.po_number}</span>
              <span className={cn("inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium", statusStyle)}>
                {order.status.replace(/_/g, " ")}
              </span>
            </div>
            <p className="mt-0.5 text-sm text-muted-foreground">{order.supplier_name}</p>
            <div className="mt-2 flex items-center gap-4 text-sm">
              <span className="font-semibold">${Number(order.total_cost).toFixed(2)}</span>
              {order.expected_date && (
                <span className="text-muted-foreground">
                  Expected: {new Date(order.expected_date).toLocaleDateString()}
                </span>
              )}
              {order.received_date && (
                <span className="text-muted-foreground">
                  Received: {new Date(order.received_date).toLocaleDateString()}
                </span>
              )}
            </div>
            <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
              <span>{order.line_items?.length || 0} line item{(order.line_items?.length || 0) !== 1 ? "s" : ""}</span>
              {order.ordered_by_name && <span>By {order.ordered_by_name}</span>}
              {order.ordered_date && <span>{new Date(order.ordered_date).toLocaleDateString()}</span>}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
