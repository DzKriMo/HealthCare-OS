# Healthcare OS — Production Readiness Plan

> Current state: MVP functional (83 tests, 110+ endpoints, Docker running on :6776).
> Goal: auditable, secure, observable, scalable production deployment.

---

## Sprint P1 — Security Hardening

**Goal**: Pass an OWASP Top 10 audit. No criticals or highs.

| # | Task | Detail |
|---|------|--------|
| P1.1 | Secrets management | Move all secrets out of `.env` files into Docker secrets or HashiCorp Vault. Rotate the dev SECRET_KEY. Inject at runtime, never in images. |
| P1.2 | TLS everywhere | Add Let's Encrypt / certbot to nginx. Redirect HTTP→HTTPS. HSTS header with 1-year max-age. |
| P1.3 | CSP headers | Content-Security-Policy header via nginx. Strict CSP: `script-src 'self'; object-src 'none'; base-uri 'self';` |
| P1.4 | Rate limiting | Add `django-ratelimit` or nginx `limit_req_zone`. Per-IP: 5 req/s. Per-endpoint overrides (login: 5/min, API keys: configurable). |
| P1.5 | CORS lockdown | Tighten `CORS_ALLOWED_ORIGINS` to explicit domains. Remove `CORS_ALLOW_ALL_ORIGINS` from dev settings. |
| P1.6 | Dependency audit | `pip-audit` + `npm audit` in CI. Block PRs with known CVEs. Schedule weekly auto-updates. |
| P1.7 | SQL injection review | Audit every raw SQL call (there are a few in audit, reports). Parameterize all queries. |
| P1.8 | JWT hardening | 32+ byte HS256 key minimum. Add `aud` (audience) validation. Add token binding (tie refresh token to client fingerprint). |
| P1.9 | File upload security | ClamAV virus scanning on all uploads. File type validation by magic bytes, not extension. Size limits enforced at nginx + Django. |
| P1.10 | Penetration test | Run OWASP ZAP against staging. Fix every medium+ finding. Document residual risks. |

---

## Sprint P2 — Observability & Monitoring

**Goal**: Know about problems before users do. Every 5xx triggers an alert within 60 seconds.

| # | Task | Detail |
|---|------|--------|
| P2.1 | Structured logging | JSON-formatted logs from Django + nginx. Include: correlation_id, tenant_id, user_id, path, method, status, duration_ms. Ship to Loki or Elasticsearch. |
| P2.2 | Metrics pipeline | Prometheus metrics endpoint on Django (`django-prometheus`). Export: request rate, error rate, latency percentiles, DB query counts, cache hit rate, Celery queue depth. |
| P2.3 | Grafana dashboards | 3 dashboards: (1) Platform Overview — requests, errors, latency, (2) Business — appointments/day, revenue/day, new patients, (3) Sync Health — queue depth, conflict rate, sync latency. |
| P2.4 | Alert rules | PagerDuty/Opsgenie alerts: API error rate > 1%, p95 latency > 1s, sync queue backlog > 500, Celery worker down > 2min, DB connection pool exhausted, disk > 85%. |
| P2.5 | Sentry integration | Wire up Django + React error boundary to Sentry. Source maps in production builds. Alert on new error types. |
| P2.6 | Health check endpoint | Enhance `/api/health/` to include: DB replication lag, Celery worker count, MinIO connectivity, Redis memory usage. Use for k8s liveness/readiness probes. |
| P2.7 | Uptime monitoring | External ping to `/api/health/` every 30s from 3 geographic regions. Alert if 2/3 regions fail. |
| P2.8 | Audit log monitoring | Alert on anomalous patterns: mass patient record access within 60s, off-hours admin actions, repeated failed logins from same IP, cross-tenant access attempts. |

---

## Sprint P3 — Database & Data Integrity

**Goal**: Proper Django migrations, automated backups with tested restore, PITR.

| # | Task | Detail |
|---|------|--------|
| P3.1 | Generate Django migrations | Run `makemigrations` for all 11 apps. Move away from `--run-syncdb` to proper migration files. Test forward + backward migrations in CI. |
| P3.2 | Migration safety CI | Run each migration against a copy of staging data. Block migrations that lock tables for > 2s or modify > 10K rows without `CONCURRENTLY`. |
| P3.3 | Backup automation | Daily full backup at 2am. WAL archiving for PITR. 30-day retention. Weekly backup restore test (automated — restore to temp DB, run tests, report). |
| P3.4 | Connection pooling | PgBouncer between Django and PostgreSQL. Pool size: 20 per worker. Statement timeout: 30s. |
| P3.5 | Query performance audit | Run `pg_stat_statements`. Find top 20 slow queries. Add missing indexes. Add `select_related`/`prefetch_related` where N+1 detected. |
| P3.6 | Read replicas | Configure Django `DATABASE_ROUTERS` to route read queries to replica. Use replica for reports, dashboard widgets, audit viewer. |
| P3.7 | Data retention policies | Define per-entity retention: audit logs (7 years), clinical records (lifetime of patient + 10 years), notifications (90 days), sync operations (30 days). Automate archival/deletion. |
| P3.8 | Encryption at rest | Verify PostgreSQL TDE or filesystem encryption. Encrypt `Patient.national_id` at application level. Verify MinIO server-side encryption. |

---

## Sprint P4 — CI/CD & Deployment

**Goal**: One-command deploy to staging. One-command promote to production. Rollback in under 2 minutes.

| # | Task | Detail |
|---|------|--------|
| P4.1 | GitHub Actions CI | All 83 tests on every PR. Type-check (mypy + tsc). Lint (ruff + eslint). Build Docker images. Block merge on failure. |
| P4.2 | Docker image pipeline | Multi-stage builds. Tag with `git sha` + `latest`. Push to private registry. Scan images with Trivy for CVEs. |
| P4.3 | Staging environment | Full replica of production at smaller scale. Deploy on every merge to main. Seed with anonymized production data. |
| P4.4 | Blue-green deploys | Two identical production stacks. Deploy to inactive, health-check, switch traffic. Rollback by switching back. |
| P4.5 | Database migration CI | Run migrations against staging before production. Generate migration report: tables locked, rows modified, estimated duration. Manual approval gate for risky migrations. |
| P4.6 | Infrastructure as Code | Terraform for: VPC, RDS, ElastiCache, ECS/EKS, S3, CloudFront. State in remote backend. Changes via PR + plan approval. |
| P4.7 | Secret rotation automation | Auto-rotate: DB passwords (monthly), JWT keys (quarterly), API keys (on revoke). Zero-downtime rotation with dual-credential windows. |

---

## Sprint P5 — Testing Completeness

**Goal**: Sleep at night. Every critical path has an automated test.

| # | Task | Detail |
|---|------|--------|
| P5.1 | E2E smoke tests | Playwright tests for: login → dashboard → create patient → create appointment → record payment → logout. Run in CI against staging. |
| P5.2 | Tenant isolation tests | Automated test: create 2 tenants. Verify tenant A cannot see tenant B's patients, appointments, invoices, documents, audit logs. Add 20+ isolation assertions. |
| P5.3 | Permission matrix tests | For each of 9 roles, assert which endpoints return 200 vs 403. Generate compliance report showing correct permission boundaries. |
| P5.4 | Load tests | k6 scripts: 500 concurrent users booking appointments. 100 concurrent practitioners writing SOAP notes. Verify p95 < 500ms under load. |
| P5.5 | Sync chaos tests | Simulate: network partition, slow connections, out-of-order operations, duplicate idempotency keys, clock skew. Verify no data loss or corruption. |
| P5.6 | Frontend unit tests | Vitest tests for: auth store, API client, branding store, error boundary, form validation. Aim for 60%+ coverage on `lib/` and `features/`. |
| P5.7 | Accessibility CI | axe-core or Lighthouse in CI. Block PRs that drop accessibility score below 90. |
| P5.8 | Contract tests | Pact or similar: verify frontend ↔ backend API contracts. Prevent breaking changes without major version bump. |

---

## Sprint P6 — Auth & Identity Hardening

**Goal**: Real MFA, proper session security, audit-grade auth.

| # | Task | Detail |
|---|------|--------|
| P6.1 | Real TOTP MFA | Replace stub MFA with `django-otp`. TOTP device management. Backup codes. MFA required for Admin + Doctor roles per tenant policy. |
| P6.2 | Brute-force protection | `django-axes` or custom: lock account for 15min after 5 failed attempts. IP-based rate limiting on login endpoint. |
| P6.3 | Session security | Refresh token rotation with reuse detection. Bind sessions to IP + User-Agent changes (re-authenticate on change). Force logout on password change (revoke all other tokens). |
| P6.4 | OAuth2 / OIDC provider | Add OAuth2 provider capability for third-party app access (SMART on FHIR preparation). Authorization code flow with PKCE. |
| P6.5 | SAML / SSO | SAML 2.0 service provider for enterprise clinics. Test with Okta, Azure AD, Google Workspace. |
| P6.6 | Password policy | Configurable per tenant: min length, complexity requirements, expiry (90 days), password history (no reuse of last 5). |
| P6.7 | Break-glass access | Emergency admin access workflow: triggers audit event + alerts all other admins. Time-limited (15 min). Auto-revokes. |

---

## Sprint P7 — Frontend Productionization

**Goal**: Production Next.js build, not dev server. Optimized bundle. Proper error states everywhere.

| # | Task | Detail |
|---|------|--------|
| P7.1 | Production build | `next build` with standalone output. Serve via nginx or `next start`. Remove dev server from production images. |
| P7.2 | Bundle optimization | Analyze bundle with `@next/bundle-analyzer`. Code-split by route. Lazy-load heavy components (odontogram, calendar). Tree-shake unused shadcn/ui components. |
| P7.3 | Caching strategy | Static assets: 1-year cache with content hash. API responses: ETag-based caching. Tenant branding: 24h cache with purge on update. |
| P7.4 | Offline support | Service worker for shell + static assets. Offline indicator in UI when API unreachable. Queue mutations locally when offline (prep for Electron sync). |
| P7.5 | Accessibility pass | Audit every page with axe-core. Fix: focus management in modals, ARIA labels on all interactive elements, color contrast on status badges, keyboard navigation on calendar and odontogram. |
| P7.6 | Loading states | Skeleton loaders for: patient list, appointment calendar, invoice table, dashboard widgets. Empty state illustrations. Error state with retry buttons + correlation IDs. |
| P7.7 | PWA readiness | Web manifest, 192px + 512px icons, `theme-color` meta, standalone display mode, offline splash screen. |

---

## Sprint P8 — HIPAA & Compliance Readiness

**Goal**: Pass a HIPAA technical assessment. Documented compliance posture.

| # | Task | Detail |
|---|------|--------|
| P8.1 | BAA-ready architecture | Document: encryption at rest + in transit, access controls, audit logging, integrity controls. Map to HIPAA Security Rule §164.312 technical safeguards. |
| P8.2 | PHI data flow map | Diagram every place PHI touches: PostgreSQL columns, Redis cache keys, MinIO objects, log files, Sentry events, email notifications. Verify all are encrypted/redacted. |
| P8.3 | Access review workflow | Quarterly access review: generate report of every user + role + permissions per tenant. Admins attest each user still needs access. |
| P8.4 | Audit log completeness | Verify every PHI access (read + write) produces an audit event. Add missing audit points: patient timeline view, document downloads, report generation. |
| P8.5 | Data export / portability | Patient data export in FHIR-compatible JSON bundle. Tenant data export for clinic offboarding. |
| P8.6 | Data deletion | Hard-delete workflow: patient requests deletion → soft-archive → 30-day grace period → irreversible anonymization. Cascade to all related entities. |
| P8.7 | Breach notification prep | Pre-built report: all patients whose data was accessed within a date range. All practitioners who accessed a specific patient. Ready to execute within 24h. |
| P8.8 | Penetration test (external) | Engage third-party security firm. Scope: API endpoints, auth flow, tenant isolation, file upload, webhook signature verification. Remediate all findings. |

---

## Sprint P9 — Electron Desktop App

**Goal**: Working Electron app with offline mode, auto-update, code signing.

| # | Task | Detail |
|---|------|--------|
| P9.1 | Electron build pipeline | `electron-builder` config. Build for Windows (.exe/.msi), macOS (.dmg), Linux (.AppImage). CI builds on all 3 platforms. |
| P9.2 | Code signing | Windows: EV code signing certificate. macOS: notarization via Apple. Auto-updater verifies signatures before applying updates. |
| P9.3 | SQLite integration | `better-sqlite3` with the full local schema. Seed with tenant's working set on first sync. WAL mode for concurrent reads during sync. |
| P9.4 | Offline workflow | Detect online/offline. Queue all mutations to `sync_queue` table. Full CRUD available offline. Visual indicator: green dot (online), amber (syncing), red (offline). |
| P9.5 | Sync client (real implementation) | Replace stubs in `sync-client.ts`. Real push/pull with the sync API. Background sync every 30s or on connectivity change. Retry with exponential backoff. |
| P9.6 | Desktop-specific features | System tray with sync status. Global shortcuts (Ctrl+Shift+P for patient search). Native print (thermal receipt, prescription, invoice). Barcode/QR scanner input. |
| P9.7 | Auto-updater | `electron-updater` with staged rollouts (10% → 50% → 100%). Forced update for critical security patches. Downgrade prevention. |

---

## Sprint P10 — Launch & Operations

**Goal**: Production launch with runbooks, SLAs, and operational maturity.

| # | Task | Detail |
|---|------|--------|
| P10.1 | Production infrastructure | Deploy to AWS/GCP: RDS PostgreSQL with Multi-AZ, ElastiCache Redis, ECS Fargate or k8s for Django + Celery, S3 for files, CloudFront CDN. |
| P10.2 | SLA targets | Publish: 99.5% uptime (monthly), p95 API latency < 200ms, Sync replay < 30s for 100 queued ops, Backup RPO < 1 hour, RTO < 4 hours. |
| P10.3 | Incident response runbook | Document: severity levels (P1-P4), escalation paths, on-call rotation, incident commander role, post-mortem template. |
| P10.4 | Disaster recovery drill | Simulate: primary DB failure. Execute: failover to replica, promote, redirect app, verify data integrity. Document time to recovery. |
| P10.5 | Capacity planning | Load test to find breaking point. Document: max concurrent users per worker, DB connections per instance size, Redis memory per 10K patients. Auto-scaling rules. |
| P10.6 | Cost optimization | Reserved instances for baseline. Spot instances for Celery workers. S3 lifecycle policies (30-day → infrequent access, 90-day → glacier). |
| P10.7 | Customer onboarding runbook | Step-by-step: create tenant → configure branding → enable modules → seed roles → invite staff → connect payment provider → go-live checklist. |
| P10.8 | Support tiers | Tier 1: front desk (password resets, booking help). Tier 2: clinic admin (role management, report configuration). Tier 3: platform engineering (sync issues, performance, bugs). |

---

## Timeline Summary

| Sprint | Focus | Estimated Weeks | Dependencies |
|--------|-------|-----------------|-------------|
| P1 | Security Hardening | 2 | — |
| P2 | Observability | 2 | — |
| P3 | Database & Data Integrity | 2 | — |
| P4 | CI/CD & Deployment | 2 | P3 (migrations) |
| P5 | Testing Completeness | 3 | P4 (CI to run tests) |
| P6 | Auth & Identity | 2 | P1 (security foundation) |
| P7 | Frontend Production | 3 | P4 (CI for builds) |
| P8 | HIPAA Compliance | 3 | P1, P2, P3 (security + audit + DB) |
| P9 | Electron Desktop | 3 | P7 (frontend prod build) |
| P10 | Launch & Operations | 2 | All of the above |

**Total: 10 sprints, ~24 weeks from MVP to production launch.**

---

## Critical Path

```
P1 (Security) ─────────────────────────────┐
P2 (Observability) ────────────────────────┤
P3 (DB & Data Integrity) ── P4 (CI/CD) ────┤── P8 (HIPAA) ── P10 (Launch)
P5 (Testing) ──────────────────────────────┤
P6 (Auth Hardening) ───────────────────────┤
P4 (CI/CD) ── P7 (Frontend) ── P9 (Desktop)┘
```

P1, P2, P3, P5, and P6 can run in parallel with separate squads.
P8 (HIPAA) should start after P1+P2+P3 foundations are in place.
P9 (Electron) depends on P7 (production frontend build).
P10 is the final integration + launch sprint.

---

## First Action (This Week)

Run the OWASP ZAP scan against the current Docker deployment on port 6776. That gives us a concrete security baseline to prioritize P1 tasks.

```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://host.docker.internal:6776 \
  -g gen.conf -r zap_report.html
```
