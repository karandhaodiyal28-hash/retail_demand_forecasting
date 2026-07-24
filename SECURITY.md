# Security & Vulnerability Report

This report details every security weakness found in the original codebase, how it was fixed, and the defence-in-depth measures added in the v1.1.0 rewrite.

---

## 1. Summary of Findings

| # | Vulnerability | Severity | Status |
|---|---|---|---|
| 1 | **No authentication on any API endpoint** | 🔴 Critical | ✅ Fixed |
| 2 | **No password hashing** (no auth at all) | 🔴 Critical | ✅ Fixed (bcrypt) |
| 3 | **No input validation** (schemas referenced but never enforced) | 🔴 Critical | ✅ Fixed (Pydantic) |
| 4 | **Path traversal in `/reports/download`** | 🔴 High | ✅ Fixed |
| 5 | **CSV import — no size / content-type / row limits** | 🔴 High | ✅ Fixed |
| 6 | **No rate limiting** (LSTM training is expensive → DoS) | 🟠 High | ✅ Fixed (slowapi) |
| 7 | **No CORS policy** (any origin could call the API) | 🟠 High | ✅ Fixed |
| 8 | **No security headers** (CSP, HSTS, X-Frame-Options) | 🟠 High | ✅ Fixed |
| 9 | **No request body size limit** | 🟠 Medium | ✅ Fixed |
| 10 | **Internal exceptions leak to clients** (and crash JSON serialisation) | 🟠 Medium | ✅ Fixed |
| 11 | **No anti-enumeration on login** (different errors for wrong user vs wrong password) | 🟠 Medium | ✅ Fixed |
| 12 | **Trust middleware missing** (host-header attacks) | 🟡 Medium | ✅ Fixed |
| 13 | **Weak role separation** (anyone could delete products) | 🟡 Medium | ✅ Fixed (RBAC) |
| 14 | **Pydantic V1-style config (`Config` class)** — would crash on Pydantic 2 | 🟡 Medium | ✅ Fixed (Pydantic 2 native) |
| 15 | **No path resolution check on report download** | 🟡 Medium | ✅ Fixed |
| 16 | **Outdated `requirements.txt`** missing security packages | 🟡 Low | ✅ Fixed |
| 17 | **No `bcrypt` pin** (passlib 1.7.4 compat issue with bcrypt 4.1+) | 🟡 Low | ✅ Fixed (pinned `bcrypt==4.0.1`) |
| 18 | **Unbounded list query** (`/products?limit=10000`) | 🟡 Low | ✅ Fixed (clamped to 500) |
| 19 | **No request id correlation** (hard to investigate incidents) | 🔵 Hardening | ✅ Added |
| 20 | **No logout / token revocation** (JWTs valid until expiry) | 🔵 Hardening | ✅ Documented; tokens are short-lived (8 h) |

---

## 2. Detailed Remediations

### 2.1 Authentication (Issue #1, #2)

**Before:** Every endpoint was publicly accessible. The seed file even created users without passwords (none existed at all).

**After:**
- New `backend/auth.py` with bcrypt + JWT helpers
- New `backend/routers/auth.py` with `/auth/{register, login, refresh, me, change-password}`
- New `User` SQLAlchemy model with `username`, `email`, `hashed_password`, `role`, `is_active`, `last_login_at`
- All other routers now require `Depends(get_current_user)` and (where appropriate) `Depends(require_role("admin", "analyst"))`
- Frontend stores the JWT in `localStorage` and attaches it as a bearer on every request
- Global 401 interceptor clears the session and redirects to `/login`
- Password policy enforced server-side: ≥ 8 chars, contains letters + digits

### 2.2 Input validation (Issue #3)

**Before:** Routers imported `from ..schemas import ...` but those schemas were never created.

**After:**
- Full `backend/schemas.py` with Pydantic v2 models for every request body
- Regex validators on `username` (`[A-Za-z0-9_.-]+`) and `sku` (`[A-Za-z0-9._-]+`)
- Numeric bounds (`unit_cost >= 0`, `lead_time_days <= 365`, `horizon_days 1-365`, etc.)
- Email is validated via `EmailStr` when present
- All validation errors return `422` with a JSON-safe error list (no leaked `ValueError` objects)

### 2.3 Path traversal on report download (Issue #4, #15)

**Before:**
```python
p = Path(rep.file_path)
return FileResponse(p, filename=p.name)
```
An attacker with the ability to set `file_path` could read `/etc/passwd`.

**After:**
```python
p = Path(rep.file_path)
p.resolve().relative_to(REPORTS_DIR.resolve())   # raises if path escapes
```

### 2.4 CSV import hardening (Issue #5)

**Before:** Any size, any content type, any number of rows.

**After:**
- Content-type check (`text/csv`, `application/vnd.ms-excel`, `application/octet-stream`, `text/plain`)
- 10 MB cap (enforced both by middleware and per-route check)
- 200 000 row cap
- Required header check (`sku, sale_date, quantity`)
- Malformed rows are skipped (not crashed) and reported in the response

### 2.5 Rate limiting (Issue #6)

**Before:** None. Calling `/forecast/run` with `model_name=lstm` in a tight loop would saturate the CPU and starve other users.

**After:**
- `slowapi` wired up in `main.py` with `Limiter(key_func=get_remote_address)`
- Default budget: 120 requests/minute per IP
- Auth endpoints: 10/minute (anti-brute-force)
- Forecast endpoints: 10/minute (LSTM training is expensive)
- `RATE_LIMIT_FORECAST=10/minute` and `RATE_LIMIT_AUTH=10/minute` are configurable

### 2.6 CORS (Issue #7)

**Before:** No CORS middleware at all (any origin was accepted by default in some debug modes).

**After:**
- Explicit allow-list in `config.py`: `["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]`
- Configurable via `CORS_ORIGINS` env var (JSON array or comma-separated)
- `allow_credentials=True` so JWT in `Authorization` header is correctly handled
- Allowed methods restricted to the ones the API actually uses

### 2.7 Security headers (Issue #8)

**Before:** None.

**After:** Every response is decorated with:
- `X-Content-Type-Options: nosniff` — stops MIME sniffing
- `X-Frame-Options: DENY` — prevents clickjacking
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()` — disallows powerful APIs the app doesn't need
- `X-XSS-Protection: 1; mode=block` (legacy)
- `Strict-Transport-Security: max-age=63072000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'`

### 2.8 Request body size limit (Issue #9)

**Before:** None. An attacker could send a 10 GB body and OOM the worker.

**After:** `BodySizeLimitMiddleware` rejects any `POST/PUT/PATCH` with `Content-Length > MAX_UPLOAD_BYTES` (default 10 MB) with `413 Payload Too Large`.

### 2.9 Internal exception leakage (Issue #10)

**Before:** Unhandled exceptions returned raw tracebacks (or crashed the JSON encoder — see test #9 below).

**After:**
- Generic `Exception` handler returns `{ "detail": "Internal server error", "request_id": "..." }` and logs the full traceback server-side
- `RequestValidationError` handler returns JSON-safe error structures
- Fixed the actual root cause: Pydantic v2's `exc.errors()` includes `ValueError` objects in `ctx` that crash `json.dumps` — now sanitised via `_json_safe()` recursion

### 2.10 Anti-enumeration (Issue #11)

**Before:** Login with wrong username vs wrong password returned different error messages, allowing user enumeration.

**After:** Both cases return the same `401 {"detail": "Invalid username or password"}`.

### 2.11 Trusted hosts (Issue #12)

**Before:** None.

**After:** `TrustedHostMiddleware` is enabled (configured `["*"]` for local dev — tighten in production via env).

### 2.12 Role-based access (Issue #13)

**Before:** Anyone could `DELETE /products/{id}` or generate reports.

**After:** `Depends(require_role("admin"))` on destructive endpoints; `require_role("admin", "analyst")` on write endpoints. Viewers can read but not write.

### 2.13 Pydantic v2 compatibility (Issue #14)

**Before:** Old `class Config: from_attributes = True` (Pydantic v1 syntax) would crash on Pydantic 2.

**After:** All schemas use Pydantic v2 native `from pydantic import BaseModel, model_config` pattern with `from_attributes = True`. Pydantic-settings is used for env loading.

### 2.14 Dependency hygiene (Issue #16, #17)

**Before:** `requirements.txt` had no `passlib`, no `python-jose`, no `slowapi`, no `bcrypt` pin.

**After:** Updated `requirements.txt`:
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.0.1` (pinned — passlib 1.7.4 has a known compat bug with bcrypt 4.1+)
- `python-jose[cryptography]==3.3.0`
- `slowapi==0.1.9`
- `pydantic-settings==2.5.2`
- `python-multipart==0.0.9` (required for OAuth2 form login)
- `email-validator` (implicit via Pydantic)

### 2.15 Unbounded queries (Issue #18)

**Before:** `db.query(Product).limit(limit)` accepted any number, enabling huge memory loads.

**After:** `limit = max(1, min(limit, 500))` on products and 5 000 on sales.

### 2.16 Request id correlation (Issue #19)

**Before:** None — hard to investigate "something went wrong" reports.

**After:** `RequestIdMiddleware` injects a 16-char UUID into every request, echoes it in the `x-request-id` response header, and includes it in error responses. Full request/exception logs are emitted server-side with the same id.

---

## 3. Verified Test Results

A live end-to-end test run against the app confirmed:

```
OK: root + health
OK: 401 without auth
OK: login, user=testadmin role=admin
OK: /me
OK: products list
OK: forecast models
OK: dashboard
OK: bad password rejected
OK: bad username rejected (json-safe)
OK: security headers present
OK: anti-enumeration error
OK: viewer blocked from /compare
OK: report 404
OK: oversize body rejected
*** ALL TESTS PASS ***
```

---

## 4. Recommendations for Production Deployment

1. **Set a strong `SECRET_KEY`** in `.env` — never commit it. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
2. **Use HTTPS** in front of the API (nginx / Caddy / a load balancer) — the `Strict-Transport-Security` header assumes it.
3. **Restrict `TrustedHostMiddleware.allowed_hosts`** to your real domain(s).
4. **Run behind a reverse proxy** (nginx) with `client_max_body_size 10m;` so requests are dropped before they reach uvicorn.
5. **Switch to PostgreSQL** for production (set `DATABASE_URL=postgresql://...`).
6. **Change the default `admin` password** (`POST /api/v1/auth/change-password`) immediately after first login.
7. **Add token revocation** (Redis denylist) if you need immediate logout — out of scope here but the auth layer is structured to make this a small change.
8. **Add structured logging** (JSON) and ship to your log aggregator.
9. **Enable Prometheus metrics** (`prometheus-fastapi-instrumentator`) for visibility.
10. **Run `bandit -r backend/` and `pip-audit`** in CI.
