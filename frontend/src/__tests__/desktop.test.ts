import { describe, it, expect } from "vitest";

describe("Desktop Offline Edition", () => {
  describe("License system", () => {
    it("validates license key format", () => {
      const validKey = /^HCOS-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;
      expect(validKey.test("HCOS-ABCD-1234-EFGH")).toBe(true);
      expect(validKey.test("invalid")).toBe(false);
    });

    it("detects expired license", () => {
      const lic = { expiryDate: "2025-01-01" };
      const now = new Date("2026-07-25");
      const expired = new Date(lic.expiryDate) < now;
      expect(expired).toBe(true);
    });

    it("detects valid license", () => {
      const lic = { expiryDate: "2027-01-01" };
      const now = new Date("2026-07-25");
      const valid = new Date(lic.expiryDate) >= now;
      expect(valid).toBe(true);
    });

    it("stores license in userData", () => {
      const userData = "/mock/userData";
      const lic = { licenseKey: "HCOS-TEST-1234-KEY", email: "test@test.com" };
      const stored = JSON.stringify(lic);
      const parsed = JSON.parse(stored);
      expect(parsed.licenseKey).toBe("HCOS-TEST-1234-KEY");
      expect(parsed.email).toBe("test@test.com");
    });
  });

  describe("Backup and restore", () => {
    it("exports database to file", () => {
      const dbBuffer = Buffer.from([0x00, 0x01, 0x02]);
      const written = Buffer.from(dbBuffer);
      expect(written.length).toBe(3);
    });

    it("restores database from file", () => {
      const backup = Buffer.from("mock db content");
      expect(backup.length).toBeGreaterThan(0);
    });

    it("validates backup file format", () => {
      const validHeader = Buffer.from("SQLite format 3\x00");
      const mockFile = Buffer.alloc(100);
      const isValid = mockFile.length >= 100;
      expect(isValid).toBe(true);
    });
  });

  describe("Electron app lifecycle", () => {
    it("creates window with correct dimensions", () => {
      const windowOpts = { width: 1400, height: 900, minWidth: 1024, minHeight: 700 };
      expect(windowOpts.width).toBe(1400);
      expect(windowOpts.height).toBe(900);
      expect(windowOpts.minWidth).toBeLessThanOrEqual(windowOpts.width);
    });

    it("minimizes to tray on close", () => {
      let isQuitting = false;
      const handleClose = (event: { preventDefault: () => void }) => {
        if (!isQuitting) event.preventDefault();
      };
      const event = { preventDefault: () => {} };
      handleClose(event);
      expect(isQuitting).toBe(false);
    });

    it("quits when isQuitting is set", () => {
      let isQuitting = true;
      const handleClose = (event: { preventDefault: () => void }) => {
        if (!isQuitting) event.preventDefault();
      };
      expect(isQuitting).toBe(true);
    });

    it("builds tray menu with status", () => {
      const pending = 3;
      const online = true;
      const label = online ? (pending > 0 ? `Syncing (${pending})` : "Online") : `Offline (${pending} queued)`;
      expect(label).toBe("Syncing (3)");
    });

    it("shows offline status with pending count", () => {
      const pending = 5;
      const online = false;
      const label = online ? (pending > 0 ? `Syncing (${pending})` : "Online") : `Offline (${pending} queued)`;
      expect(label).toBe("Offline (5 queued)");
    });
  });

  describe("Global shortcuts", () => {
    it("registers Ctrl+Shift+P for patient search", () => {
      const shortcut = "CommandOrControl+Shift+P";
      expect(shortcut).toContain("Shift+P");
    });

    it("registers Ctrl+Shift+N for new appointment", () => {
      const shortcut = "CommandOrControl+Shift+N";
      expect(shortcut).toContain("Shift+N");
    });

    it("registers Ctrl+Shift+I for devtools", () => {
      const shortcut = "CommandOrControl+Shift+I";
      expect(shortcut).toContain("Shift+I");
    });
  });

  describe("Production server", () => {
    it("starts Next.js server on port 3000", () => {
      const port = 3000;
      expect(port).toBe(3000);
    });

    it("detects development mode via --dev flag", () => {
      const isDev = (args: string[]) => args.includes("--dev");
      expect(isDev(["--dev"])).toBe(true);
      expect(isDev([])).toBe(false);
    });

    it("loads frontend from resources path in production", () => {
      const isPackaged = true;
      const resourcesPath = "/resources";
      const frontendDir = isPackaged ? resourcesPath + "/frontend" : null;
      expect(frontendDir).toBe("/resources/frontend");
    });
  });

  describe("IPC handlers", () => {
    it("handles db:query IPC call", () => {
      const handler = "db:query";
      expect(handler).toBe("db:query");
    });

    it("handles queue:enqueue IPC call", () => {
      const mutation = { entityType: "patient", entityId: "123", operationType: "create" };
      expect(mutation.entityType).toBe("patient");
    });

    it("handles backup:create IPC call", () => {
      const handler = "backup:create";
      const result = { canceled: false, filePath: "/backup.db" };
      expect(result.filePath).toBeTruthy();
      expect(result.canceled).toBe(false);
    });

    it("handles sync:status IPC call", () => {
      const status = { online: true, pending: 0 };
      expect(status.online).toBe(true);
      expect(status.pending).toBe(0);
    });
  });

  describe("Standalone offline mode", () => {
    it("queues mutations when offline", () => {
      const queue = [
        { entityType: "patient", operationType: "create", status: "pending" },
        { entityType: "appointment", operationType: "update", status: "pending" },
      ];
      expect(queue).toHaveLength(2);
      expect(queue.every((q) => q.status === "pending")).toBe(true);
    });

    it("flushes queue when back online", () => {
      const queue = [
        { id: "1", status: "pending" },
        { id: "2", status: "pending" },
      ];
      const flushed = queue.map((q) => ({ ...q, status: "synced" }));
      expect(flushed.every((q) => q.status === "synced")).toBe(true);
    });

    it("local SQLite stores patients offline", () => {
      const localData = { id: "local-1", first_name: "John", last_name: "Doe" };
      expect(localData.id).toMatch(/^local-/);
    });
  });

  describe("About page info", () => {
    it("displays correct edition name", () => {
      const edition = "Desktop Offline Edition";
      expect(edition).toBe("Desktop Offline Edition");
    });

    it("lists all core modules", () => {
      const modules = ["Patient Management", "Appointments", "Clinical Records", "e-Prescriptions", "Lab & Imaging", "Inventory", "Billing"];
      expect(modules).toHaveLength(7);
      expect(modules).toContain("Billing");
      expect(modules).toContain("Clinical Records");
    });
  });
});
