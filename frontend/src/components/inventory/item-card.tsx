"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  unit: string;
  sku: string;
  barcode: string;
  quantity_on_hand: number;
  reorder_point: number;
  reorder_quantity: number;
  unit_cost: string;
  unit_price: string;
  requires_batch_tracking: boolean;
  requires_refrigeration: boolean;
  is_low_stock: boolean;
  stock_value: string;
  supplier: string;
  supplier_name: string;
  is_active: boolean;
  notes: string;
}

interface ItemCardProps {
  item: InventoryItem;
  onClick: () => void;
}

const CATEGORY_STYLES: Record<string, string> = {
  medicine: "bg-red-100 text-red-700",
  supply: "bg-blue-100 text-blue-700",
  equipment: "bg-purple-100 text-purple-700",
  consumable: "bg-amber-100 text-amber-700",
  other: "bg-gray-100 text-gray-700",
};

export function ItemCard({ item, onClick }: ItemCardProps) {
  const categoryStyle = CATEGORY_STYLES[item.category] || CATEGORY_STYLES.other;

  return (
    <Card className="cursor-pointer transition-colors hover:border-primary" onClick={onClick}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="truncate font-medium">{item.name}</span>
              <span className={cn("inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium", categoryStyle)}>
                {item.category}
              </span>
              {item.requires_refrigeration && (
                <span className="text-[10px] text-blue-600">❄</span>
              )}
            </div>
            {item.sku && (
              <p className="mt-0.5 text-xs text-muted-foreground">SKU: {item.sku}</p>
            )}
            <div className="mt-2 flex items-center gap-4 text-sm">
              <span className={cn("font-semibold", item.is_low_stock && "text-destructive")}>
                Qty: {item.quantity_on_hand}
              </span>
              <span className="text-muted-foreground">Reorder: {item.reorder_point}</span>
              {item.unit && <span className="text-muted-foreground">Unit: {item.unit}</span>}
            </div>
            <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
              {item.unit_cost && <span>Cost: ${Number(item.unit_cost).toFixed(2)}</span>}
              {item.supplier_name && <span>Supplier: {item.supplier_name}</span>}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
