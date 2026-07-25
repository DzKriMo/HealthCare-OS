import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatName, formatDisplayId } from "@/lib/utils";
import { patientDemographicsSchema, patientContactSchema } from "@healthcare-os/validators";

describe("Patient form validation", () => {
  describe("demographicsSchema", () => {
    it("accepts valid demographics", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "Doe",
        date_of_birth: "1990-01-15",
        gender: "male",
        blood_type: "A+",
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(true);
    });

    it("rejects missing first name", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "",
        last_name: "Doe",
        date_of_birth: "1990-01-15",
        gender: "male",
        blood_type: null,
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].path).toContain("first_name");
      }
    });

    it("rejects missing last name", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "",
        date_of_birth: "1990-01-15",
        gender: "male",
        blood_type: null,
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(false);
    });

    it("rejects invalid date format", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "Doe",
        date_of_birth: "01/15/1990",
        gender: "male",
        blood_type: null,
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(false);
    });

    it("rejects invalid gender", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "Doe",
        date_of_birth: "1990-01-15",
        gender: "alien",
        blood_type: null,
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(false);
    });

    it("accepts nullable blood type", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "Doe",
        date_of_birth: "1990-01-15",
        gender: "male",
        blood_type: null,
        marital_status: "single",
        national_id: null,
      });
      expect(result.success).toBe(true);
    });

    it("accepts valid blood type values", () => {
      for (const bt of ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] as const) {
        const result = patientDemographicsSchema.safeParse({
          first_name: "John",
          last_name: "Doe",
          date_of_birth: "1990-01-15",
          gender: "male",
          blood_type: bt,
          marital_status: "single",
          national_id: null,
        });
        expect(result.success).toBe(true);
      }
    });

    it("rejects invalid marital status", () => {
      const result = patientDemographicsSchema.safeParse({
        first_name: "John",
        last_name: "Doe",
        date_of_birth: "1990-01-15",
        gender: "male",
        blood_type: null,
        marital_status: "complicated",
        national_id: null,
      });
      expect(result.success).toBe(false);
    });
  });

  describe("contactSchema", () => {
    it("accepts valid contact", () => {
      const result = patientContactSchema.safeParse({
        phone: "+1-555-123-4567",
        email: null,
        address_line1: "123 Main St",
        address_line2: null,
        city: "New York",
        state: "NY",
        postal_code: "10001",
        country: "US",
      });
      expect(result.success).toBe(true);
    });

    it("rejects short phone", () => {
      const result = patientContactSchema.safeParse({
        phone: "12",
        email: null,
        address_line1: "123 Main St",
        address_line2: null,
        city: "New York",
        state: null,
        postal_code: null,
        country: "US",
      });
      expect(result.success).toBe(false);
    });

    it("validates email format when provided", () => {
      const result = patientContactSchema.safeParse({
        phone: "+1-555-123-4567",
        email: "not-an-email",
        address_line1: "123 Main St",
        address_line2: null,
        city: "New York",
        state: null,
        postal_code: null,
        country: "US",
      });
      expect(result.success).toBe(false);
    });

    it("rejects missing address", () => {
      const result = patientContactSchema.safeParse({
        phone: "+1-555-123-4567",
        email: null,
        address_line1: "",
        address_line2: null,
        city: "New York",
        state: null,
        postal_code: null,
        country: "US",
      });
      expect(result.success).toBe(false);
    });
  });
});

describe("Patient display utilities", () => {
  it("formatName builds full name from components", () => {
    expect(formatName("John", "Doe")).toBe("John Doe");
    expect(formatName("Jane", "Smith")).toBe("Jane Smith");
  });

  it("formatName handles missing parts", () => {
    expect(formatName(null, "Doe")).toBe("Doe");
    expect(formatName("John", null)).toBe("John");
    expect(formatName(null, null)).toBe("\u2014");
    expect(formatName(undefined, undefined)).toBe("\u2014");
  });

  it("formatDisplayId generates correct formats", () => {
    expect(formatDisplayId("PAT", 2024, 1)).toBe("PAT-2024-0001");
    expect(formatDisplayId("PAT", 2024, 42)).toBe("PAT-2024-0042");
    expect(formatDisplayId("INV", 2024, 9999)).toBe("INV-2024-9999");
  });
});

describe("Search debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("delays search execution by 300ms", () => {
    const searchFn = vi.fn();
    let timer: ReturnType<typeof setTimeout>;

    const simulateTyping = (query: string) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => searchFn(query), 300);
    };

    simulateTyping("John");
    expect(searchFn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);
    expect(searchFn).toHaveBeenCalledWith("John");
    expect(searchFn).toHaveBeenCalledTimes(1);
  });

  it("cancels previous search on new input", () => {
    const searchFn = vi.fn();
    let timer: ReturnType<typeof setTimeout>;

    const simulateTyping = (query: string) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => searchFn(query), 300);
    };

    simulateTyping("Jo");
    vi.advanceTimersByTime(200);
    simulateTyping("Joh");
    vi.advanceTimersByTime(200);
    simulateTyping("John");
    vi.advanceTimersByTime(300);

    expect(searchFn).toHaveBeenCalledTimes(1);
    expect(searchFn).toHaveBeenCalledWith("John");
  });
});

describe("Paginated patient data", () => {
  it("calculates total pages correctly", () => {
    const PAGE_SIZE = 20;
    expect(Math.max(1, Math.ceil(0 / PAGE_SIZE))).toBe(1);
    expect(Math.max(1, Math.ceil(1 / PAGE_SIZE))).toBe(1);
    expect(Math.max(1, Math.ceil(20 / PAGE_SIZE))).toBe(1);
    expect(Math.max(1, Math.ceil(21 / PAGE_SIZE))).toBe(2);
    expect(Math.max(1, Math.ceil(100 / PAGE_SIZE))).toBe(5);
  });

  it("calculates offset correctly", () => {
    const PAGE_SIZE = 20;
    expect((1 - 1) * PAGE_SIZE).toBe(0);
    expect((2 - 1) * PAGE_SIZE).toBe(20);
    expect((5 - 1) * PAGE_SIZE).toBe(80);
  });

  it("handles edge case: page cannot be less than 1", () => {
    expect(Math.max(1, 0)).toBe(1);
    expect(Math.max(1, -1)).toBe(1);
    expect(Math.max(1, 1)).toBe(1);
    expect(Math.max(1, 5)).toBe(5);
  });

  it("handles edge case: page cannot exceed total pages", () => {
    const totalPages = 5;
    expect(Math.min(5, totalPages)).toBe(5);
    expect(Math.min(1, totalPages)).toBe(1);
    expect(Math.min(10, totalPages)).toBe(5);
  });
});
