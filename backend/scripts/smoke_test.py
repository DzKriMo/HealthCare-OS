"""
API smoke test — verifies every endpoint returns the expected status code.

Usage:
    python scripts/smoke_test.py              # against localhost:8000
    python scripts/smoke_test.py --base http://staging:8000

Requires: requests (`pip install requests`)
"""
import argparse
import sys
import time
import requests

BASE = "http://localhost:8000"
TIMEOUT = 10
PASS = 0
FAIL = 0


def test(method: str, path: str, expected: int | list[int], **kwargs):
    global PASS, FAIL
    url = f"{BASE}{path}"
    try:
        r = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        status = r.status_code
        ok = status == expected if isinstance(expected, int) else status in expected
        label = "✅" if ok else "❌"
        if ok:
            PASS += 1
        else:
            FAIL += 1
        print(f"  {label} {method.upper():6s} {path:50s} → {status} (expected {expected})")
    except Exception as e:
        FAIL += 1
        print(f"  ❌ {method.upper():6s} {path:50s} → ERROR: {e}")


def main():
    global BASE
    parser = argparse.ArgumentParser(description="Healthcare OS API smoke test")
    parser.add_argument("--base", default=BASE, help="Base URL")
    args = parser.parse_args()
    BASE = args.base.rstrip("/")

    print(f"\n🔍 Healthcare OS API Smoke Test — {BASE}\n")

    # ── Health ──────────────────────────────────────────────
    print("\n── Health & Discovery ──")
    test("GET", "/api/health/", 200)
    test("GET", "/api/schema/", 200)
    test("GET", "/api/docs/", 200)

    # ── Auth (unauthenticated) ──────────────────────────────
    print("\n── Auth (unauthenticated) ──")
    test("POST", "/api/auth/login/", 400, json={})
    test("POST", "/api/auth/login/", 400, json={"email": "x@y.com", "password": "wrong"})
    test("POST", "/api/auth/token/refresh/", 400, json={})
    test("POST", "/api/auth/password/reset/", 200, json={"email": "x@y.com", "tenant_slug": "test"})

    # ── Authenticated flows ─────────────────────────────────
    print("\n── Auth (authenticated) ──")
    r = requests.post(f"{BASE}/api/auth/login/", json={
        "email": "admin@smileclinic.com",
        "password": "demopass123",
        "tenant_slug": "smile-dental",
    }, timeout=TIMEOUT)
    if r.status_code == 200:
        data = r.json()
        token = data["tokens"]["access"]
        refresh = data["tokens"]["refresh"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  ✅ Login successful — got token")

        test("GET", "/api/auth/users/me/", 200, headers=headers)
        test("GET", "/api/auth/roles/", 200, headers=headers)
        test("GET", "/api/auth/permissions/", 200, headers=headers)
        test("GET", "/api/auth/sessions/", 200, headers=headers)
        test("GET", "/api/auth/users/", 200, headers=headers)

        # ── Core domains ────────────────────────────────────
        print("\n── Core Domains ──")
        test("GET", "/api/patients/", 200, headers=headers)
        test("GET", "/api/appointments/", 200, headers=headers)
        test("GET", "/api/billing/invoices/", 200, headers=headers)
        test("GET", "/api/billing/items/", 200, headers=headers)
        test("GET", "/api/audit/", 200, headers=headers)
        test("GET", "/api/notifications/", 200, headers=headers)
        test("GET", "/api/documents/", 200, headers=headers)
        test("GET", "/api/sync/pull/", 200, headers=headers)

        # ── Specialty modules ───────────────────────────────
        print("\n── Specialty Modules ──")
        test("GET", "/api/clinical/", 200, headers=headers)
        test("GET", "/api/dental/", 200, headers=headers)
        test("GET", "/api/inventory/", 200, headers=headers)
        test("GET", "/api/pharmacy/", 200, headers=headers)
        test("GET", "/api/lab/", 200, headers=headers)
        test("GET", "/api/imaging/", 200, headers=headers)
        test("GET", "/api/derm/", 200, headers=headers)
        test("GET", "/api/ophth/", 200, headers=headers)
        test("GET", "/api/cardio/", 200, headers=headers)

        # ── Protected endpoints (should 403 without perms) ──
        print("\n── Permission Enforcement ──")
        test("POST", "/api/auth/roles/", [403, 400], headers=headers, json={"name": "test", "permission_ids": []})
        test("POST", "/api/auth/roles/", [403, 400], headers=headers, json={"name": "", "permission_ids": []})

        # ── Logout ──────────────────────────────────────────
        print("\n── Logout ──")
        test("POST", "/api/auth/logout/", 200, headers=headers, json={"refresh": refresh})
    else:
        print(f"  ❌ Login failed ({r.status_code}): {r.text[:200]}")
        test("POST", "/api/auth/login/", 200, json={
            "email": "admin@smileclinic.com",
            "password": "demopass123",
            "tenant_slug": "smile-dental",
        })

    # ── Summary ─────────────────────────────────────────────
    total = PASS + FAIL
    print(f"\n{'═' * 60}")
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed")
    if FAIL > 0:
        print(f"  ❌ SMOKE TEST FAILED")
        sys.exit(1)
    else:
        print(f"  ✅ ALL SMOKE TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
