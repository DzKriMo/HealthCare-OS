# Healthcare OS — MVP Launch Checklist

## Pre-Launch Verification

### Security
- [ ] Django SECRET_KEY is 50+ chars, generated fresh for production
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS restricted to actual domains
- [ ] CORS_ALLOWED_ORIGINS restricted to actual frontend origins
- [ ] JWT access token lifetime: 15 minutes
- [ ] Argon2 password hashing enabled
- [ ] TLS certificates installed and valid
- [ ] Security headers present (HSTS, X-Frame-Options, CSP)
- [ ] API keys stored hashed (never in plaintext)
- [ ] Audit events are immutable (delete protection verified)

### Database
- [ ] PostgreSQL PITR (Point-in-Time Recovery) enabled
- [ ] Daily automated backups configured
- [ ] Backup restoration tested within last 30 days
- [ ] All tenant_id columns indexed
- [ ] Connection pooling configured (PgBouncer) for production scale

### Sync & Offline
- [ ] Device registration flow tested
- [ ] Push operations idempotent (verified via duplicate test)
- [ ] Conflict detection working for versioned entities
- [ ] Manual review triggered for clinical conflicts
- [ ] Sync pull returns correct changes since cursor

### Testing
- [ ] 83/83 backend tests passing
- [ ] Frontend type-check passing (tsc --noEmit)
- [ ] E2E smoke tests passing (login → dashboard → create patient → create appointment)
- [ ] Tenant isolation verified (cross-tenant access blocked)
- [ ] Permission enforcement verified (403 for missing perms)

### Performance
- [ ] API p95 latency < 200ms for reads
- [ ] API p95 latency < 500ms for writes
- [ ] Dashboard widgets render < 2s
- [ ] File upload supports 100MB (DICOM)
- [ ] Page load LCP < 2.5s

### Accessibility
- [ ] Lighthouse accessibility score ≥ 90
- [ ] Keyboard navigation works on login, dashboard, patient list
- [ ] Color contrast ratios meet WCAG AA
- [ ] Screen reader tested on critical forms

### Module Registry
- [ ] Dental module enables/disables correctly
- [ ] Menu items appear/disappear based on enabled modules
- [ ] Permissions registered by dental module are enforced
- [ ] New specialty can be added without core code changes

### API & Integrations
- [ ] OpenAPI docs accessible at /api/docs/
- [ ] API key generation works (full key shown only once)
- [ ] API key authentication works with scoped permissions
- [ ] Webhook registration and HMAC signing verified
- [ ] Rate limiting functional (100 req/hour per API key)

### White-Label
- [ ] Tenant branding changes reflected in UI (logo, colors, clinic name)
- [ ] Branding persists across page navigation
- [ ] Custom domain resolution works (if configured)

### Monitoring
- [ ] Health check endpoint responds: {"status": "healthy"}
- [ ] Sentry configured for error tracking
- [ ] Prometheus metrics endpoint accessible
- [ ] Alert rules configured (sync failures, billing errors, auth spikes)

## Go/No-Go Decision

### GO if:
- [ ] All 83 tests pass
- [ ] Security checklist complete
- [ ] Performance targets met
- [ ] Backup/restore tested
- [ ] Tenant isolation verified
- [ ] Dental module workflow complete (chart → procedure → plan)
- [ ] Sync push/pull functional with 2+ devices

### NO-GO if:
- [ ] Any clinical data integrity issue found
- [ ] Cross-tenant data leakage detected
- [ ] Sync conflict causes data loss
- [ ] Billing calculation error found
- [ ] Security vulnerability (OWASP Top 10) unpatched

## Post-Launch (Week 1)

- [ ] Monitor error rates hourly
- [ ] Review audit logs for anomalies
- [ ] Check sync telemetry — any devices failing?
- [ ] Verify billing invoices match expected amounts
- [ ] Respond to first support tickets

## Post-Launch (Month 1)

- [ ] Performance review — identify slow queries
- [ ] User feedback collection
- [ ] Plan Sprint 11 (Phase 2 modules: Lab, Pharmacy, Imaging)
- [ ] Review conflict resolution rules effectiveness
- [ ] Security penetration test
