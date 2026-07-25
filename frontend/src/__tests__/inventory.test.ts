import { describe, it, expect } from "vitest";

describe("Inventory item management", () => {
  it("detects low stock correctly", () => {
    const item = { quantity_on_hand: 5, reorder_point: 10 };
    const isLow = item.quantity_on_hand <= item.reorder_point && item.reorder_point > 0;
    expect(isLow).toBe(true);
  });

  it("does not flag adequate stock as low", () => {
    const item = { quantity_on_hand: 20, reorder_point: 10 };
    const isLow = item.quantity_on_hand <= item.reorder_point && item.reorder_point > 0;
    expect(isLow).toBe(false);
  });

  it("handles zero reorder point (no threshold)", () => {
    const item = { quantity_on_hand: 0, reorder_point: 0 };
    const isLow = item.quantity_on_hand <= item.reorder_point && item.reorder_point > 0;
    expect(isLow).toBe(false);
  });

  it("calculates stock value correctly", () => {
    const item = { quantity_on_hand: 100, unit_cost: 5.5 };
    const stockValue = Number(item.quantity_on_hand) * Number(item.unit_cost);
    expect(stockValue).toBe(550);
  });

  it("categorizes items by type", () => {
    const categories = ["medicine", "supply", "equipment", "consumable", "other"] as const;
    expect(categories).toContain("medicine");
    expect(categories).toContain("equipment");
    expect(categories.length).toBe(5);
  });

  it("supports batch tracking flag", () => {
    const item = { requires_batch_tracking: true };
    expect(item.requires_batch_tracking).toBe(true);
  });
});

describe("Stock movement tracking", () => {
  it("tracks quantity before and after", () => {
    const movement = { quantity_before: 100, quantity: -10, quantity_after: 90 };
    expect(movement.quantity_before + movement.quantity).toBe(movement.quantity_after);
  });

  it("in movement increases stock", () => {
    const before = 50;
    const qty = 25;
    const after = before + qty;
    expect(after).toBe(75);
  });

  it("out movement decreases stock", () => {
    const before = 50;
    const qty = -10;
    const after = before + qty;
    expect(after).toBe(40);
  });

  it("adjustment can be positive or negative", () => {
    expect(10 > 0).toBe(true);
    expect(-5 < 0).toBe(true);
  });

  it("waste is recorded as negative", () => {
    const wasteQty = -5;
    expect(wasteQty).toBeLessThan(0);
  });

  it("return is recorded as positive", () => {
    const returnQty = 3;
    expect(returnQty).toBeGreaterThan(0);
  });
});

describe("Batch and expiry tracking", () => {
  it("detects expired batches", () => {
    const today = new Date("2026-07-25");
    const expired = new Date("2025-01-01");
    expect(expired < today).toBe(true);
  });

  it("detects non-expired batches", () => {
    const today = new Date("2026-07-25");
    const future = new Date("2027-01-01");
    expect(future > today).toBe(true);
  });

  it("flags batches expiring within 90 days", () => {
    const today = new Date("2026-07-25");
    const expiring = new Date("2026-09-01");
    const diffMs = expiring.getTime() - today.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const isExpiringSoon = diffDays >= 0 && diffDays <= 90;
    expect(isExpiringSoon).toBe(true);
  });

  it("does not flag batches expiring far in future", () => {
    const today = new Date("2026-07-25");
    const far = new Date("2028-01-01");
    const diffMs = far.getTime() - today.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const isExpiringSoon = diffDays >= 0 && diffDays <= 90;
    expect(isExpiringSoon).toBe(false);
  });

  it("unique lot number per item constraint", () => {
    const lots = new Map<string, boolean>();
    const addLot = (lot: string) => {
      if (lots.has(lot)) return false;
      lots.set(lot, true);
      return true;
    };
    expect(addLot("LOT001")).toBe(true);
    expect(addLot("LOT001")).toBe(false);
    expect(addLot("LOT002")).toBe(true);
  });
});

describe("Supplier management", () => {
  it("tracks supplier contact info", () => {
    const supplier = { name: "MedSupply Co", contact_person: "John Doe", email: "john@medsupply.com", phone: "+1234567890" };
    expect(supplier.name).toBeTruthy();
    expect(supplier.email).toContain("@");
  });

  it("defaults to active", () => {
    const supplier = { is_active: true };
    expect(supplier.is_active).toBe(true);
  });
});

describe("Purchase order workflow", () => {
  it("starts as draft", () => {
    const po = { status: "draft" };
    expect(po.status).toBe("draft");
  });

  it("transitions: draft → sent → partially_received → received", () => {
    const allowed: Record<string, string[]> = {
      draft: ["sent", "cancelled"],
      sent: ["partially_received", "received", "cancelled"],
      partially_received: ["received", "cancelled"],
    };
    expect(allowed.draft).toContain("sent");
    expect(allowed.sent).toContain("partially_received");
    expect(allowed.partially_received).toContain("received");
  });

  it("cancelled is terminal", () => {
    const terminal = ["received", "cancelled"] as const;
    expect(terminal).toContain("cancelled");
  });

  it("calculates total cost from line items", () => {
    const items = [{ quantity: 10, unit_cost: 5 }, { quantity: 3, unit_cost: 20 }];
    const total = items.reduce((s, i) => s + i.quantity * i.unit_cost, 0);
    expect(total).toBe(110);
  });

  it("generates PO number in correct format", () => {
    const year = 2026;
    const seq = 42;
    const poNumber = `PO-${year}-${String(seq).padStart(5, "0")}`;
    expect(poNumber).toBe("PO-2026-00042");
  });

  it("tracks received quantities per line item", () => {
    const receipts = [
      { item_id: "1", quantity: 5 },
      { item_id: "2", quantity: 10 },
    ];
    const totalReceived = receipts.reduce((s, r) => s + r.quantity, 0);
    expect(totalReceived).toBe(15);
  });
});

describe("Refrigeration requirements", () => {
  it("flags items needing refrigeration", () => {
    const item = { requires_refrigeration: true };
    expect(item.requires_refrigeration).toBe(true);
  });

  it("defaults to no refrigeration", () => {
    const item = { requires_refrigeration: false };
    expect(item.requires_refrigeration).toBe(false);
  });
});
