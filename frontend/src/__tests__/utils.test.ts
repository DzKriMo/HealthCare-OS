import { describe, it, expect } from "vitest";
import { formatName, formatDisplayId } from "@/lib/utils";
import { cn } from "@/lib/utils";

describe("formatName", () => {
  it("joins first and last name", () => {
    expect(formatName("John", "Doe")).toBe("John Doe");
  });

  it("handles null values", () => {
    expect(formatName(null, "Doe")).toBe("Doe");
    expect(formatName("John", null)).toBe("John");
    expect(formatName(null, null)).toBe("—");
  });

  it("handles undefined values", () => {
    expect(formatName(undefined, "Doe")).toBe("Doe");
    expect(formatName("John", undefined)).toBe("John");
  });
});

describe("formatDisplayId", () => {
  it("formats with zero-padded sequence", () => {
    expect(formatDisplayId("PAT", 2024, 1)).toBe("PAT-2024-0001");
    expect(formatDisplayId("PAT", 2024, 100)).toBe("PAT-2024-0100");
    expect(formatDisplayId("INV", 2024, 9999)).toBe("INV-2024-9999");
  });
});

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible");
  });

  it("resolves tailwind conflicts", () => {
    expect(cn("px-4", "px-2")).toBe("px-2");
  });
});
