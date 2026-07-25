"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

const DOMAINS = [
  {
    title: "Identity & RBAC",
    desc: "JWT authentication, 2FA, 46 granular permissions, 9 system roles, tenant isolation.",
    icon: "🔐",
    sprint: 1,
  },
  {
    title: "Patient Master Data",
    desc: "FHIR-compatible records, versioned medical history, consents, insurance, full-text search.",
    icon: "👤",
    sprint: 2,
  },
  {
    title: "Appointments & Queue",
    desc: "Day/week/month calendar, conflict detection, 7-state status machine, live queue board.",
    icon: "📅",
    sprint: 3,
  },
  {
    title: "Billing & Payments",
    desc: "Quote→Invoice→Payment, POS checkout, tax engine, refunds, revenue dashboard.",
    icon: "💳",
    sprint: 4,
  },
  {
    title: "Files & Notifications",
    desc: "S3/MinIO storage, signed URLs, multi-channel orchestration, template engine.",
    icon: "📁",
    sprint: 5,
  },
  {
    title: "Audit & Reports",
    desc: "Immutable audit trail, 5 report types, role-aware dashboard with 6 widget types.",
    icon: "📊",
    sprint: 6,
  },
  {
    title: "Dental Module",
    desc: "32-tooth FDI odontogram, 14 procedure types, implants, crowns, treatment plans.",
    icon: "🦷",
    sprint: 7,
  },
  {
    title: "API & Webhooks",
    desc: "API keys with scoped permissions, HMAC-signed webhooks, self-service booking tokens.",
    icon: "🔗",
    sprint: 8,
  },
  {
    title: "Offline Sync",
    desc: "Push/pull engine, 5 conflict strategies, idempotency, SQLite local mirror.",
    icon: "🔄",
    sprint: 9,
  },
];

const STATS = [
  { label: "API Endpoints", value: "110+" },
  { label: "Test Suite", value: "83/83" },
  { label: "Domain Apps", value: "11" },
  { label: "DB Tables", value: "47" },
];

export default function HomePage() {
  const router = useRouter();
  const [health, setHealth] = useState<{ status: string; checks?: { database?: string; redis?: string } } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      router.push("/dashboard");
      return;
    }
    fetch("/api/health/")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => {});
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      {/* ── Nav ─────────────────────────────────────────── */}
      <nav className="flex items-center justify-between px-6 py-4 border-b">
        <div className="flex items-center gap-3">
          <Image
            src="/logo.png"
            alt="Healthcare OS"
            width={36}
            height={36}
            className="rounded-lg"
          />
          <span className="text-lg font-semibold tracking-tight">
            Healthcare OS
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/api/docs/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            API Docs
          </Link>
          <Link
            href="/admin/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Admin
          </Link>
          <Link
            href="/login"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="px-6 py-20 text-center">
        <div className="mx-auto max-w-3xl space-y-6">
          <Image
            src="/logo.png"
            alt="Healthcare OS"
            width={72}
            height={72}
            className="mx-auto rounded-2xl shadow-lg"
            priority
          />
          <h1 className="text-5xl font-bold tracking-tight">
            Healthcare Operating System
          </h1>
          <p className="text-xl text-muted-foreground leading-relaxed">
            A modular, offline-first, multi-tenant platform that scales from a
            single dental clinic to a multi-specialty hospital network — all on
            one codebase.
          </p>
          <div className="flex gap-4 justify-center pt-4">
            <Link
              href="/login"
              className="rounded-lg bg-primary px-8 py-3 text-base font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg shadow-primary/25"
            >
              Sign In to Demo
            </Link>
            <Link
              href="/api/docs/"
              className="rounded-lg border px-8 py-3 text-base font-medium hover:bg-accent transition-colors"
            >
              Explore the API
            </Link>
          </div>
          {process.env.NEXT_PUBLIC_SHOW_DEMO_CREDS === "true" && (
            <p className="text-xs text-muted-foreground">
              Demo credentials: admin@smileclinic.com / demopass123
            </p>
          )}
        </div>
      </section>

      {/* ── Status Bar ───────────────────────────────────── */}
      <section className="px-6 pb-8">
        <div className="mx-auto max-w-3xl">
          <div className="grid grid-cols-4 gap-3">
            {STATS.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border bg-card p-4 text-center"
              >
                <div className="text-2xl font-bold text-primary">
                  {stat.value}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
          {health && (
            <div className="mt-3 flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <span
                className={`inline-block h-2 w-2 rounded-full ${
                  health.status === "healthy" ? "bg-green-500" : "bg-red-500"
                }`}
              />
              Backend: {health.status} · DB: {health.checks?.database || "—"} ·
              Redis: {health.checks?.redis || "—"}
            </div>
          )}
        </div>
      </section>

      {/* ── Domains Grid ─────────────────────────────────── */}
      <section className="px-6 pb-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-2xl font-bold text-center mb-8">
            What&apos;s Built
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {DOMAINS.map((domain) => (
              <div
                key={domain.title}
                className="group rounded-xl border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-md"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{domain.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm">{domain.title}</h3>
                    <span className="text-xs text-muted-foreground">
                      Sprint {domain.sprint}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {domain.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="border-t px-6 py-8 text-center text-xs text-muted-foreground">
        <p>
          Healthcare OS · 10 sprints · 83 tests · 110+ API endpoints ·{" "}
          <Link href="/api/docs/" className="underline hover:text-foreground">
            OpenAPI Docs
          </Link>
        </p>
      </footer>
    </div>
  );
}
