# Architecture

## High-level

```
┌──────────────────────────────────────────────────────────────┐
│                        React Frontend                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────────┐   │
│  │ Login   │→ │Sidebar  │→ │ Topbar  │→ │ Pages (Glass)  │   │
│  └─────────┘  └─────────┘  └─────────┘  └────────────────┘   │
│       ↓ AuthContext  ↓ ToastContext   ↓ Axios+JWT            │
└────────────────────────┬─────────────────────────────────────┘
                         │  /api/v1/*   (Bearer token)
┌────────────────────────┴─────────────────────────────────────┐
│                       FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Middleware   │→ │ Routers      │→ │ Services           │   │
│  │ CORS, SecHdr,│  │ /auth        │  │ Prophet/XGB/LSTM   │   │
│  │ BodySize,    │  │ /products    │  │ Inventory          │   │
│  │ TrustedHost  │  │ /sales       │  │ Reports            │   │
│  │ RateLimit    │  │ /forecast    │  │                    │   │
│  └──────────────┘  │ /inventory   │  └────────────────────┘   │
│         ↓          │ /reports     │            ↓              │
│     Auth(JWT)      │ /dashboard   │        ┌─────────────┐     │
│                    └──────┬───────┘        │ SQLAlchemy  │     │
│                           ↓                │ ORM         │     │
│                     Pydantic schemas       └──────┬──────┘     │
└───────────────────────────────────────────────────┼───────────┘
                                                    ↓
                                          ┌──────────────────┐
                                          │  SQLite/Postgres │
                                          │  data/retail.db  │
                                          └──────────────────┘
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `backend/main.py` | App factory, middleware, exception handlers, router mounting |
| `backend/config.py` | Centralised settings (env-driven) |
| `backend/database.py` | SQLAlchemy engine + `get_db` dependency |
| `backend/models.py` | ORM tables: `User`, `Product`, `Sale`, `Forecast`, `Inventory`, `Report` |
| `backend/schemas.py` | Pydantic request/response models with validation |
| `backend/auth.py` | bcrypt + JWT helpers, `get_current_user`, `require_role` |
| `backend/routers/*` | One file per resource; thin HTTP layer |
| `backend/services/*` | Business logic, ML model wrappers, report generation |
| `backend/utils/*` | Pure helpers: MAE/RMSE/MAPE, seasonal decomposition |
| `backend/seed_data.py` | 20 products + 400 days of sales + default admin |

## Request lifecycle

1. **CORS preflight** (if cross-origin) — handled by `CORSMiddleware`
2. **TrustedHost** — block obvious host-header attacks
3. **SecurityHeaders** — strip anything dangerous, set CSP/HSTS/etc.
4. **RequestId** — tag the request for correlation
5. **BodySizeLimit** — reject oversize payloads with 413
6. **SlowAPI** — apply per-IP rate limit
7. **Router** — match route, run dependencies
8. **Auth dependency** — decode JWT, fetch `User` from DB
9. **Pydantic** — validate request body / query
10. **Service** — execute business logic
11. **Response** — wrap in Pydantic model, return JSON

## Security layers (defence-in-depth)

```
Network:    HTTPS (nginx) → HSTS header → TrustedHost
AuthN:      JWT (HS256) → bcrypt(12) password hash → role check
AuthZ:      require_role("admin", "analyst") per endpoint
Input:      Pydantic regex/length/bound checks
DoS:        BodySizeLimit middleware + slowapi rate limit + row caps
Data:       SQLAlchemy ORM (no raw SQL) → SQL injection-proof
Output:     JSON-safe error responses → no info leakage
Audit:      last_login_at + report.created_by; future: full event log
```
