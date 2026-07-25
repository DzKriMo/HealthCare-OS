# Healthcare OS — Admin Runbook

## Tenant Provisioning

### Create a new tenant

```bash
# Via Django management command (recommended)
docker compose exec backend python manage.py shell -c "
from tenancy.models import Tenant, TenantSettings
t = Tenant.objects.create(
    slug='new-clinic',
    name='New Clinic',
    branding={'primary_color': '#0369a1', 'clinic_name': 'New Clinic'},
    enabled_modules=['dental', 'billing', 'documents'],
)
TenantSettings.objects.create(tenant=t)
print(f'Tenant created: {t.id}')
"
```

### Provision admin user for tenant

```bash
docker compose exec backend python manage.py seed_roles  # Once: seed base roles
docker compose exec backend python manage.py shell -c "
from identity.models import User, Role
from tenancy.models import Tenant
tenant = Tenant.objects.get(slug='new-clinic')
admin_role = Role.objects.get(name='Admin', is_system_role=True)
user = User.objects.create_user(
    email='admin@newclinic.com', password='changeme1234567890',
    first_name='Admin', last_name='User', tenant=tenant, role=admin_role,
)
print(f'User created: {user.email}')
"
```

### Enable/disable modules for a tenant

```bash
docker compose exec backend python manage.py shell -c "
from tenancy.models import Tenant
t = Tenant.objects.get(slug='smile-dental')
t.enabled_modules = ['dental', 'billing', 'documents', 'notifications', 'imaging']
t.save(update_fields=['enabled_modules'])
"
```

## Backup and Restore

### PostgreSQL backup

```bash
# Full dump
docker compose exec db pg_dump -U healthcare_os healthcare_os > backup_$(date +%Y%m%d).sql

# Schema + data, compressed
docker compose exec db pg_dump -U healthcare_os healthcare_os | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Automated backup (cron)

```bash
# Add to crontab (daily at 2am)
0 2 * * * cd /opt/healthcare-os && docker compose exec -T db pg_dump -U healthcare_os healthcare_os | gzip > /backups/healthcare_os_$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
# Restore from backup
docker compose exec -T db psql -U healthcare_os healthcare_os < backup_20260723.sql

# Restore compressed
gunzip -c backup_20260723.sql.gz | docker compose exec -T db psql -U healthcare_os healthcare_os
```

### Object storage backup (MinIO/S3)

```bash
# Sync objects to backup location
aws s3 sync s3://healthcare-os-prod/ s3://healthcare-os-backup/ --endpoint-url=https://minio.example.com
```

## Monitoring & Alerts

### Health check

```bash
curl https://app.healthcare-os.com/api/health/
# Expected: {"status":"healthy","checks":{"database":"ok","redis":"ok"}}
```

### Key metrics to monitor

| Metric | Alert threshold | Action |
|--------|----------------|--------|
| API latency p95 | > 500ms | Check DB query performance, add index |
| Sync queue backlog | > 1000 ops | Check device connectivity, sync engine |
| Failed sync rate | > 5% | Check conflict resolution, device registration |
| Billing API errors | Any | Immediate investigation |
| Auth failures spike | > 10/min | Possible brute force — check rate limiting |
| Disk usage | > 80% | Expand volume or clean old backups |
| Celery queue depth | > 1000 | Add workers or check stuck tasks |

### Prometheus metrics (available at /metrics)

- `http_requests_total{method, path, status}`
- `http_request_duration_seconds{method, path}`
- `sync_operations_total{status, entity_type}`
- `sync_conflicts_total{entity_type}`
- `celery_tasks_total{task_name, state}`

## Incident Response

### Scenario 1: Sync engine failing

1. Check sync status: `GET /api/sync/status/?device_id=...`
2. Check conflict rules: `GET /api/sync/conflict-rules/`
3. Review recent failures: Django admin → Sync Operations → filter by status=failed
4. Common fix: set conflict rule to `last_write_wins` temporarily for non-clinical entities
5. For clinical conflicts: manually review each conflict entry

### Scenario 2: Tenant cannot log in

1. Verify tenant is active: `Tenant.objects.get(slug='x').is_active`
2. Verify user is active: `User.objects.get(email='x').is_active`
3. Check failed login attempts (rate limiting)
4. Reset MFA if needed: set `user.mfa_enabled = False`, clear `user.mfa_secret`

### Scenario 3: Performance degradation

1. Check PostgreSQL slow queries: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 seconds';`
2. Check Redis memory: `docker compose exec redis redis-cli INFO memory`
3. Check Celery worker count: increase `-c` parameter in docker-compose
4. Add missing database indexes — check query plans with `EXPLAIN ANALYZE`

## Scaling Checklist

- [ ] Increase Celery workers: `docker compose up -d --scale worker=4`
- [ ] Add PostgreSQL read replicas (update DATABASE_URL)
- [ ] Increase Redis maxmemory
- [ ] Add CDN for static assets
- [ ] Enable database connection pooling (PgBouncer)
- [ ] Review and add database indexes for slow queries

## Security

### Rotate secrets

```bash
# Generate new Django secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Update in .env and restart
docker compose up -d backend
```

### Audit key rotation checklist

- [ ] Django SECRET_KEY
- [ ] JWT signing key
- [ ] MinIO access keys
- [ ] Database passwords
- [ ] SMTP credentials
- [ ] SMS provider API keys
