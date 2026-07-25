"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";

interface RevenueData {
  total_revenue: string;
  total_collected: string;
  total_outstanding: string;
  invoice_count: number;
  payment_count: number;
}

export function RevenueWidgets() {
  const [data, setData] = useState<RevenueData | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setData(await api.get<RevenueData>("/billing/revenue/?period=month"));
      } catch { }
    };
    load();
  }, []);

  if (!data) return null;

  const widgets = [
    { label: "Revenue (month)", value: `$${Number(data.total_collected).toFixed(2)}`, icon: "creditCard", color: "text-green-600" },
    { label: "Invoiced", value: `$${Number(data.total_revenue).toFixed(2)}`, icon: "fileText", color: "text-blue-600" },
    { label: "Outstanding", value: `$${Number(data.total_outstanding).toFixed(2)}`, icon: "bell", color: "text-amber-600" },
    { label: "Invoices", value: String(data.invoice_count), icon: "barChart", color: "text-purple-600" },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {widgets.map((w) => {
        const Icon = Icons[w.icon as keyof typeof Icons] || Icons.creditCard;
        return (
          <Card key={w.label}>
            <CardContent className="flex items-center gap-3 p-4">
              <div className={`rounded-lg p-2 ${w.color} bg-opacity-10`}>
                <Icon className={`h-5 w-5 ${w.color}`} />
              </div>
              <div>
                <div className="text-xl font-bold">{w.value}</div>
                <div className="text-xs text-muted-foreground">{w.label}</div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
