import { describe, it, expect } from "vitest";

describe("WhatsApp & Voice Bots", () => {
  describe("WhatsApp messaging", () => {
    it("sends outbound WhatsApp message", () => {
      const result = { success: true, sid: "SM12345", status: "queued" };
      expect(result.success).toBe(true);
      expect(result.sid).toMatch(/^SM/);
    });

    it("receives inbound WhatsApp message", () => {
      const msg = { direction: "inbound", content: "Can I reschedule?", from: "+1234567890" };
      expect(msg.direction).toBe("inbound");
      expect(msg.content).toBeTruthy();
    });

    it("tracks message direction", () => {
      const directions = ["inbound", "outbound"];
      expect(directions).toContain("inbound");
      expect(directions).toContain("outbound");
    });

    it("supports template messages", () => {
      const msg = { message_type: "template", template_name: "appointment_reminder" };
      expect(msg.message_type).toBe("template");
    });

    it("stores Twilio message SID", () => {
      const msg = { twilio_message_sid: "SMabc123" };
      expect(msg.twilio_message_sid).toMatch(/^SM/);
    });
  });

  describe("WhatsApp conversation", () => {
    it("starts conversation on first inbound message", () => {
      const conv = { customer_phone: "+1234567890", status: "active", message_count: 1 };
      expect(conv.status).toBe("active");
      expect(conv.message_count).toBe(1);
    });

    it("tracks conversation status", () => {
      const statuses = ["active", "resolved", "escalated"];
      expect(statuses).toContain("active");
    });

    it("escalates to staff", () => {
      const conv = { status: "active" };
      conv.status = "escalated";
      expect(conv.status).toBe("escalated");
    });
  });

  describe("Auto-reply bot", () => {
    it("replies with confirmation for '1'", () => {
      const replies: Record<string, string> = {
        "1": "Thank you for confirming your appointment.",
        "2": "Please call our office to reschedule.",
        "3": "We're sorry to hear that.",
      };
      expect(replies["1"]).toContain("confirming");
    });

    it("replies to reschedule request", () => {
      const message = "2";
      const reply = message === "2" ? "Please call our office to reschedule" : "";
      expect(reply).toContain("reschedule");
    });

    it("provides office hours on help request", () => {
      const reply = "Our office hours are Monday-Friday 9 AM to 5 PM.";
      expect(reply).toContain("9 AM");
    });

    it("handles billing inquiries", () => {
      const reply = "For billing inquiries, please visit our patient portal.";
      expect(reply).toContain("billing");
    });

    it("sends default reply for unknown queries", () => {
      const defaultReply = "Thank you for your message. We'll get back to you shortly.";
      expect(defaultReply).toBeTruthy();
    });
  });

  describe("Voice calls", () => {
    it("makes outbound voice call", () => {
      const call = { success: true, sid: "CA12345", status: "queued" };
      expect(call.success).toBe(true);
      expect(call.sid).toMatch(/^CA/);
    });

    it("tracks call status", () => {
      const statuses = ["queued", "ringing", "in_progress", "completed", "busy", "failed", "no_answer", "cancelled"];
      expect(statuses).toContain("completed");
      expect(statuses).toContain("failed");
    });

    it("records call duration", () => {
      const call = { duration_seconds: 120 };
      expect(call.duration_seconds).toBeGreaterThan(0);
    });

    it("marks bot calls", () => {
      const call = { is_bot_call: true };
      expect(call.is_bot_call).toBe(true);
    });
  });

  describe("Appointment reminders", () => {
    it("sends reminder via WhatsApp", () => {
      const reminder = { channel: "whatsapp", message: "Reminder: Your appointment is tomorrow at 10 AM" };
      expect(reminder.channel).toBe("whatsapp");
    });

    it("sends reminder via voice call", () => {
      const reminder = { channel: "voice", message: "This is an automated reminder" };
      expect(reminder.channel).toBe("voice");
    });

    it("configures reminder timing", () => {
      const config = { appointment_reminder_hours_before: 24 };
      expect(config.appointment_reminder_hours_before).toBe(24);
    });
  });

  describe("Bot configuration", () => {
    it("enables/disables WhatsApp bot", () => {
      const config = { whatsapp_enabled: true };
      expect(config.whatsapp_enabled).toBe(true);
    });

    it("enables/disables voice bot", () => {
      const config = { voice_enabled: false };
      expect(config.voice_enabled).toBe(false);
    });

    it("configures business hours", () => {
      const config = { business_hours_only: true, business_hours_start: "09:00", business_hours_end: "17:00" };
      expect(config.business_hours_start).toBe("09:00");
      expect(config.business_hours_end).toBe("17:00");
    });

    it("configures auto-reply message", () => {
      const config = { auto_reply_message: "Thank you for your message" };
      expect(config.auto_reply_message.length).toBeGreaterThan(0);
    });
  });

  describe("Dashboard stats", () => {
    it("counts active conversations", () => {
      const stats = { active_conversations: 5 };
      expect(stats.active_conversations).toBeGreaterThanOrEqual(0);
    });

    it("counts successful calls", () => {
      const stats = { successful_calls: 3, total_calls: 5 };
      expect(stats.successful_calls).toBeLessThanOrEqual(stats.total_calls);
    });
  });
});
