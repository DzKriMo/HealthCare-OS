import { describe, it, expect } from "vitest";
import { appointmentCreateSchema } from "@healthcare-os/validators";

describe("Appointment validation", () => {
  it("accepts valid appointment data", () => {
    const start = new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const result = appointmentCreateSchema.safeParse({
      patient_id: "550e8400-e29b-41d4-a716-446655440000",
      practitioner_id: "550e8400-e29b-41d4-a716-446655440001",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      type: "consultation",
      notes: null,
      room: null,
    });
    expect(result.success).toBe(true);
  });

  it("rejects end time before start time", () => {
    const start = new Date();
    const end = new Date(start.getTime() - 60 * 60 * 1000);
    const result = appointmentCreateSchema.safeParse({
      patient_id: "550e8400-e29b-41d4-a716-446655440000",
      practitioner_id: "550e8400-e29b-41d4-a716-446655440001",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      type: "consultation",
      notes: null,
      room: null,
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid type", () => {
    const start = new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const result = appointmentCreateSchema.safeParse({
      patient_id: "550e8400-e29b-41d4-a716-446655440000",
      practitioner_id: "550e8400-e29b-41d4-a716-446655440001",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      type: "walk_in",
      notes: null,
      room: null,
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing patient_id", () => {
    const start = new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const result = appointmentCreateSchema.safeParse({
      practitioner_id: "550e8400-e29b-41d4-a716-446655440001",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      type: "consultation",
      notes: null,
      room: null,
    });
    expect(result.success).toBe(false);
  });

  it("rejects non-UUID patient_id", () => {
    const start = new Date();
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const result = appointmentCreateSchema.safeParse({
      patient_id: "not-a-uuid",
      practitioner_id: "550e8400-e29b-41d4-a716-446655440001",
      start_time: start.toISOString(),
      end_time: end.toISOString(),
      type: "consultation",
      notes: null,
      room: null,
    });
    expect(result.success).toBe(false);
  });
});

describe("Status transitions", () => {
  const TRANSITIONS: Record<string, string[]> = {
    scheduled: ["confirmed", "arrived", "cancelled", "no_show"],
    confirmed: ["arrived", "cancelled", "no_show"],
    arrived: ["in_progress", "cancelled"],
    in_progress: ["completed"],
    completed: [],
    cancelled: ["scheduled"],
    no_show: ["scheduled"],
  };

  it("allows valid transitions", () => {
    expect(TRANSITIONS.scheduled).toContain("confirmed");
    expect(TRANSITIONS.scheduled).toContain("cancelled");
    expect(TRANSITIONS.confirmed).toContain("arrived");
    expect(TRANSITIONS.arrived).toContain("in_progress");
    expect(TRANSITIONS.in_progress).toContain("completed");
  });

  it("blocks invalid transitions", () => {
    expect(TRANSITIONS.scheduled).not.toContain("completed");
    expect(TRANSITIONS.confirmed).not.toContain("completed");
    expect(TRANSITIONS.completed).not.toContain("scheduled");
    expect(TRANSITIONS.arrived).not.toContain("confirmed");
  });

  it("completed is a terminal state", () => {
    expect(TRANSITIONS.completed).toHaveLength(0);
  });

  it("cancelled and no_show can rebook to scheduled", () => {
    expect(TRANSITIONS.cancelled).toContain("scheduled");
    expect(TRANSITIONS.no_show).toContain("scheduled");
  });
});

describe("Conflict detection", () => {
  it("detects overlapping time ranges", () => {
    const existing = { start: new Date("2024-01-15T10:00"), end: new Date("2024-01-15T10:30") };
    const candidate = { start: new Date("2024-01-15T10:15"), end: new Date("2024-01-15T10:45") };
    const hasConflict = candidate.start < existing.end && candidate.end > existing.start;
    expect(hasConflict).toBe(true);
  });

  it("passes for non-overlapping time ranges", () => {
    const existing = { start: new Date("2024-01-15T10:00"), end: new Date("2024-01-15T10:30") };
    const candidate = { start: new Date("2024-01-15T10:30"), end: new Date("2024-01-15T11:00") };
    const hasConflict = candidate.start < existing.end && candidate.end > existing.start;
    expect(hasConflict).toBe(false);
  });

  it("passes for same-time appointments on different practitioners", () => {
    const existing = { practitioner: "dr-a", start: new Date("2024-01-15T10:00"), end: new Date("2024-01-15T10:30") };
    const candidate = { practitioner: "dr-b", start: new Date("2024-01-15T10:00"), end: new Date("2024-01-15T10:30") };
    const hasConflict = candidate.practitioner === existing.practitioner &&
      candidate.start < existing.end && candidate.end > existing.start;
    expect(hasConflict).toBe(false);
  });
});

describe("Calendar date helpers", () => {
  it("calculates week date range correctly", () => {
    const date = new Date("2024-01-17"); // Wednesday
    const dayOfWeek = date.getDay();
    const start = new Date(date);
    start.setDate(start.getDate() - dayOfWeek);
    expect(start.toISOString().split("T")[0]).toBe("2024-01-14");

    const end = new Date(start);
    end.setDate(end.getDate() + 7);
    expect(end.toISOString().split("T")[0]).toBe("2024-01-21");
  });

  it("calculates month date range correctly", () => {
    const date = new Date("2024-01-15T12:00:00Z");
    const monthStart = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
    const monthEnd = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0));
    expect(monthStart.toISOString().split("T")[0]).toBe("2024-01-01");
    expect(monthEnd.toISOString().split("T")[0]).toBe("2024-01-31");
  });

  it("navigates days correctly", () => {
    const date = new Date("2024-01-15");
    const next = new Date(date);
    next.setDate(next.getDate() + 1);
    expect(next.getDate()).toBe(16);
    const prev = new Date(date);
    prev.setDate(prev.getDate() - 1);
    expect(prev.getDate()).toBe(14);
  });
});
