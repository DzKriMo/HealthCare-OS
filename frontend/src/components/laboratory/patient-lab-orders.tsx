"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Icons } from "@/components/icons";
import { api } from "@/lib/api/client";
import { LabOrderCard } from "@/components/laboratory/lab-order-card";

interface LabOrderSummary {
  id: string; patient_name: string; patient_id: string;
  status: string; priority: string;
  test_names: string[]; ordered_at: string;
  ordered_by_name?: string;
}

interface Props { patientId: string; }

export function PatientLabOrders({ patientId }: Props) {
  const router = useRouter();
  const [orders, setOrders] = useState<LabOrderSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.get<{ results: LabOrderSummary[] }>(`/lab/orders/?patient=${patientId}`);
        setOrders(data.results);
      } catch { } finally { setLoading(false); }
    };
    load();
  }, [patientId]);

  if (loading) return <Card><CardContent><div className="h-20 animate-pulse rounded-lg bg-muted" /></CardContent></Card>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Lab Orders</CardTitle>
          <p className="text-sm text-muted-foreground">{orders.length} order{orders.length !== 1 ? "s" : ""}</p>
        </div>
        <Button size="sm" onClick={() => router.push(`/lab/orders/new?patient=${patientId}`)}>
          <Icons.plus className="mr-1 h-4 w-4" /> New Order
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {orders.length === 0 ? (
          <p className="text-sm text-muted-foreground">No lab orders.</p>
        ) : (
          orders.map((o) => (
            <LabOrderCard key={o.id} order={o} onClick={() => router.push(`/lab/orders/${o.id}`)} />
          ))
        )}
      </CardContent>
    </Card>
  );
}
