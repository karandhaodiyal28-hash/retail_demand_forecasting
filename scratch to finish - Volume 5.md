# Retail Demand Forecasting — Complete Learning Document (Volume 5)

> **Sections 23–26: Source Code Map, Glossary, Interview Questions, Learning Notes**

---

## Section 23 — Complete Source Code Map

### 23.1 File Import Dependency Graph

```mermaid
graph TB
    subgraph Backend Core
        config[config.py]
        database[database.py]
        models[models.py]
        schemas[schemas.py]
        auth[auth.py]
        main[main.py]
    end
    subgraph Routers
        r_auth[routers/auth.py]
        r_prod[routers/products.py]
        r_sales[routers/sales.py]
        r_fc[routers/forecast.py]
        r_inv[routers/inventory.py]
        r_rep[routers/reports.py]
        r_dash[routers/dashboard.py]
    end
    subgraph Services
        s_fc[services/forecast_service.py]
        s_inv[services/inventory_service.py]
        s_prophet[services/prophet_service.py]
        s_xgb[services/xgboost_service.py]
        s_lstm[services/lstm_service.py]
        s_rep[services/report_service.py]
    end
    subgraph Utils
        u_metrics[utils/metrics.py]
        u_seasonal[utils/seasonal.py]
    end

    database --> config
    models --> database
    auth --> config
    auth --> database
    auth --> models
    main --> config
    main --> database
    main --> r_auth
    main --> r_prod
    main --> r_sales
    main --> r_fc
    main --> r_inv
    main --> r_rep
    main --> r_dash

    r_auth --> database
    r_auth --> models
    r_auth --> schemas
    r_auth --> auth
    r_auth --> config

    r_prod --> database
    r_prod --> models
    r_prod --> schemas
    r_prod --> auth

    r_sales --> database
    r_sales --> models
    r_sales --> schemas
    r_sales --> auth
    r_sales --> config

    r_fc --> database
    r_fc --> models
    r_fc --> schemas
    r_fc --> auth
    r_fc --> config
    r_fc --> s_fc
    r_fc --> u_seasonal

    r_inv --> database
    r_inv --> models
    r_inv --> schemas
    r_inv --> auth
    r_inv --> s_inv

    r_rep --> database
    r_rep --> models
    r_rep --> schemas
    r_rep --> auth
    r_rep --> s_rep
    r_rep --> config

    r_dash --> database
    r_dash --> models
    r_dash --> auth

    s_fc --> models
    s_fc --> config
    s_fc --> s_prophet
    s_fc --> s_xgb
    s_fc --> s_lstm

    s_prophet --> config
    s_prophet --> u_metrics

    s_xgb --> config
    s_xgb --> u_metrics

    s_lstm --> config
    s_lstm --> u_metrics

    s_inv --> models
    s_inv --> config

    s_rep --> models
    s_rep --> config
    s_rep --> s_inv
    s_rep --> u_seasonal
```

### 23.2 Frontend Component Dependency Graph

```mermaid
graph TB
    subgraph Entry
        main_jsx[main.jsx]
        app[App.jsx]
    end
    subgraph Providers
        auth_ctx[AuthContext.jsx]
        toast_ctx[ToastContext.jsx]
    end
    subgraph Layout
        sidebar[Sidebar.jsx]
        topbar[Topbar.jsx]
        protected[ProtectedRoute.jsx]
    end
    subgraph Pages
        login[Login.jsx]
        dashboard[Dashboard.jsx]
        forecast[Forecast.jsx]
        inventory[Inventory.jsx]
        sales[Sales.jsx]
        products[Products.jsx]
        seasonal[Seasonal.jsx]
        reports[Reports.jsx]
    end
    subgraph API
        client[api/client.js]
        useApi[useApi.js]
    end

    main_jsx --> app
    app --> auth_ctx
    app --> toast_ctx
    app --> sidebar
    app --> topbar
    app --> protected
    app --> login
    app --> dashboard
    app --> forecast
    app --> inventory
    app --> sales
    app --> products
    app --> seasonal
    app --> reports
    app --> client

    protected --> auth_ctx
    sidebar --> auth_ctx
    topbar --> auth_ctx
    login --> client
    login --> auth_ctx
    login --> toast_ctx
    dashboard --> client
    dashboard --> useApi
    forecast --> client
    forecast --> toast_ctx
    inventory --> client
    sales --> client
    products --> client
    seasonal --> client
    reports --> client
    reports --> toast_ctx
```

### 23.3 API Call Chain

| Frontend Action | API Function | Backend Router | Service | Database |
|----------------|-------------|----------------|---------|----------|
| Login | `endpoints.login()` | `routers/auth.login()` | `auth.verify_password()` | `SELECT users` |
| View products | `endpoints.listProducts()` | `routers/products.list_products()` | Direct query | `SELECT products` |
| Run forecast | `endpoints.runForecast()` | `routers/forecast.run()` | `forecast_service.run_forecast()` | `SELECT sales`, `DELETE/INSERT forecasts` |
| Compare models | `endpoints.compareModels()` | `routers/forecast.compare()` | `forecast_service.compare_models()` | Same as above ×3 |
| View inventory | `endpoints.listInventory()` | `routers/inventory.list_inventory()` | `inventory_service.get_all_inventory_status()` | `SELECT products, sales, inventory` |
| Generate report | `endpoints.generateReport()` | `routers/reports.generate()` | `report_service.generate_*_report()` | `SELECT` + file write |
| Download report | `endpoints.downloadReport()` | `routers/reports.download()` | Path check | File read |
| Dashboard summary | `endpoints.dashboardSummary()` | `routers/dashboard.summary()` | Aggregation queries | `SELECT + GROUP BY` |

### 23.4 Database Call Chain by Endpoint

| Endpoint | SQL Operations |
|----------|---------------|
| POST /auth/login | `SELECT users WHERE username=?` → `UPDATE users SET last_login_at` |
| POST /auth/register | `SELECT users WHERE username=?` → `INSERT users` |
| GET /products | `SELECT products LIMIT ? OFFSET ?` |
| POST /products | `SELECT products WHERE sku=?` → `INSERT products` |
| POST /forecast/run | `SELECT products WHERE id=?` → `SELECT sales WHERE product_id=? ORDER BY sale_date` → `DELETE forecasts WHERE product_id=? AND model_name=?` → `INSERT forecasts (×horizon)` |
| GET /inventory | For each product: `SELECT sales WHERE product_id=?` → compute stats |
| POST /reports/generate | Varies by type → `INSERT reports` |
| GET /dashboard/summary | `COUNT products` → `COUNT sales` → `SUM revenue` → `SELECT forecasts LIMIT 500` → `JOIN products+sales GROUP BY category` |

---

## Section 24 — Glossary

### Technical Terms

| Term | Simple Explanation | Technical Definition |
|------|-------------------|---------------------|
| **API** | A way for programs to talk to each other | Application Programming Interface — defines endpoints, methods, and data formats |
| **REST** | Rules for building web APIs | Representational State Transfer — stateless, resource-based architecture |
| **JWT** | A digital ticket proving your identity | JSON Web Token — signed JSON payload with claims (sub, exp, etc.) |
| **bcrypt** | A password scrambler that's hard to reverse | Adaptive hash function based on Blowfish cipher |
| **ORM** | Lets you use Python objects instead of SQL | Object-Relational Mapping — maps classes to tables |
| **CRUD** | The 4 basic database operations | Create, Read, Update, Delete |
| **Middleware** | Code that runs between request and handler | Intercepts every request for cross-cutting concerns |
| **CORS** | Rules about which websites can call your API | Cross-Origin Resource Sharing — browser security policy |
| **CSP** | Rules about what scripts/styles a page can load | Content Security Policy — HTTP header for XSS prevention |
| **HSTS** | Forces HTTPS connections | HTTP Strict Transport Security |
| **Rate Limiting** | Limits how many requests per time period | Prevents abuse/DoS by capping request frequency |
| **Dependency Injection** | Passing dependencies instead of creating them | FastAPI's `Depends()` pattern |
| **Pydantic** | Auto-validates data against a schema | Python data validation using type annotations |
| **Schema** | A description of what data looks like | Defines fields, types, constraints |
| **Migration** | Updating database structure without losing data | Schema versioning (Alembic for SQLAlchemy) |
| **Endpoint** | A specific URL that accepts requests | URL + HTTP method combination |
| **Router** | Groups related endpoints together | FastAPI APIRouter for modular code |
| **Service** | Business logic separated from HTTP concerns | Pure functions that implement features |
| **Decorator** | Modifies function behavior | `@router.get("/")` transforms a function into a route handler |
| **Context** | Shared state in React | React Context API — avoids prop drilling |
| **Hook** | Reusable stateful logic in React | `useApi`, `useAuth`, `useToast` |
| **Interceptor** | Code that runs on every request/response | Axios interceptors for JWT and error handling |
| **Proxy** | Forwards requests to another server | Vite dev proxy: 5173 → 8000 |
| **Time Series** | Data points ordered by time | Daily sales quantities over 400 days |
| **Seasonality** | Repeating patterns in time series | Weekly (weekends higher) or monthly patterns |
| **Trend** | Long-term direction of data | Increasing or decreasing over time |
| **MAE** | Average prediction error (absolute) | Mean Absolute Error |
| **RMSE** | Average prediction error (squared, penalizes big errors) | Root Mean Squared Error |
| **MAPE** | Average prediction error as percentage | Mean Absolute Percentage Error |
| **Safety Stock** | Extra inventory buffer for uncertainty | Z × σ × √(lead_time) |
| **Reorder Point** | Stock level that triggers a new order | avg_daily × lead + safety_stock |
| **Lead Time** | Days between ordering and receiving goods | Supplier delivery time |
| **SKU** | Unique product identifier code | Stock Keeping Unit |
| **Lag Feature** | Past values used as model inputs | lag_7 = value from 7 days ago |
| **Rolling Mean** | Average over a sliding window | Last 7 days average |
| **Z-score** | How many standard deviations from mean | (x - μ) / σ |
| **Normalization** | Scaling data to similar ranges | Z-score: (x - mean) / std |
| **Recursive Forecast** | Using predictions as future inputs | Each prediction feeds back as next lag |
| **EarlyStopping** | Stop training when model stops improving | Keras callback that monitors validation loss |
| **Epoch** | One pass through entire training data | 20 epochs = 20 full passes |
| **Batch Size** | Samples processed before weight update | 16 samples per gradient step |
| **Glassmorphism** | Frosted glass visual effect | `backdrop-filter: blur()` + semi-transparent background |

---

## Section 25 — Interview Questions

### 25.1 Project-Level Questions (20)

**Q1: What is the purpose of this project?**
A: It's an AI/ML-powered demand forecasting and inventory optimization platform for retail businesses. It predicts future product demand using three ML models (Prophet, XGBoost, LSTM), provides inventory reorder recommendations, and offers an executive dashboard for decision-making.

**Q2: What tech stack does this project use?**
A: Backend: Python 3.12 + FastAPI + SQLAlchemy + Pydantic. Frontend: React 18 + Vite + Recharts + Axios. ML: Prophet + XGBoost + TensorFlow/LSTM. Database: SQLite (dev) / PostgreSQL (prod). Auth: JWT + bcrypt.

**Q3: How does the project handle authentication?**
A: OAuth2 password flow with JWT. User submits credentials → server verifies bcrypt hash → issues access token (8hr) and refresh token (7d). Every subsequent request includes Bearer token. Token decoded on each request to identify user and role.

**Q4: What are the three ML models used and when would you choose each?**
A: Prophet — products with strong seasonality + missing data tolerance. XGBoost — products with rich feature interactions and 30+ days history. LSTM — products with complex non-linear patterns and 60+ days history. The compare endpoint runs all three and picks the best by RMSE.

**Q5: How is inventory optimization implemented?**
A: Safety Stock = Z(1.65) × σ_daily × √(lead_time). Reorder Point = avg_daily × lead + safety_stock. Status: REORDER (below safety), LOW (below reorder point), OVERSTOCK (3× above reorder), OK. These are computed dynamically from sales history.

**Q6: How does the project handle security?**
A: Multiple layers: JWT auth, bcrypt passwords (12 rounds), rate limiting (slowapi), security headers (CSP, HSTS, X-Frame-Options), body size limits, path-traversal protection on downloads, input validation (Pydantic), generic error messages (no leakage).

**Q7: What design patterns are used?**
A: Registry Pattern (MODEL_REGISTRY), Dependency Injection (FastAPI Depends), Provider Pattern (React Context), Interceptor Pattern (Axios), Factory Pattern (require_role()), Singleton (settings with lru_cache), Repository Pattern (services encapsulate DB access).

**Q8: How does the frontend communicate with the backend?**
A: Axios HTTP client with request interceptor (auto-attaches JWT), response interceptor (handles 401). In development, Vite proxy forwards /api/v1/* from :5173 to :8000. All endpoints defined in client.js as named functions.

**Q9: Explain the database schema.**
A: 6 tables: users (auth), products (catalog), sales (daily transactions), forecasts (ML predictions), inventory (stock levels), reports (generated files). Products has cascade relationships to sales/forecasts/inventory. Composite indexes on frequent query patterns.

**Q10: How would you scale this for production?**
A: 1) Switch to PostgreSQL, 2) Add Gunicorn with multiple workers, 3) Move LSTM training to background workers (Celery + Redis), 4) Add caching (Redis) for dashboard queries, 5) Deploy frontend to CDN (Vercel), 6) Add database connection pooling.

### 25.2 Backend Questions (20)

**Q11: What is FastAPI's dependency injection system?**
A: `Depends()` creates a dependency chain. When a route needs a DB session, it uses `Depends(get_db)`. For auth, `Depends(get_current_user)` which itself depends on `Depends(oauth2_scheme)` and `Depends(get_db)`. Dependencies are resolved automatically and cached per request.

**Q12: How does the rate limiter work?**
A: slowapi uses the client's IP address (from `get_remote_address`) as the key. Counts requests per IP per time window. If limit exceeded, returns HTTP 429. Config: 120/min default, 10/min for auth and forecast endpoints.

**Q13: Why are custom Swagger docs routes used?**
A: Browser dark-mode makes default Swagger UI text invisible. Custom routes inject CSS forcing light backgrounds. Also, strict CSP blocks CDN-loaded scripts — docs routes use a relaxed CSP allowing cdn.jsdelivr.net while API routes keep strict CSP.

**Q14: How does the exception handler prevent information leakage?**
A: Generic handler catches all unhandled exceptions, logs the full error server-side with request ID, but returns only `{"detail": "Internal server error", "request_id": "..."}` to the client. No stack traces, no file paths, no internal state exposed.

**Q15: Explain SQLAlchemy session management.**
A: `get_db()` is a generator dependency. Creates a session (SessionLocal()), yields it to the handler, and guarantees `db.close()` in the finally block. This prevents connection leaks even if the handler raises an exception.

**Q16: What is `cascade="all, delete-orphan"`?**
A: When a parent (Product) is deleted, all children (Sales, Forecasts) are automatically deleted (cascade). "delete-orphan" also deletes children that are removed from the parent's collection (disassociated).

**Q17: How does pydantic-settings work?**
A: `Settings(BaseSettings)` reads from environment variables and .env file. Each field name matches an env var (case-sensitive). Field validators can transform values (e.g., CORS_ORIGINS comma-string → list). `@lru_cache` ensures single instance.

**Q18: Why is `pool_pre_ping=True` used?**
A: It tests database connections before using them. If the connection is stale (server restarted, timeout), it reconnects automatically. Prevents "connection refused" errors on long-idle connections.

**Q19: How does CSV import handle errors gracefully?**
A: Content-type check → size check → UTF-8 decode → header validation → per-row processing with try/except (skips bad rows) → returns count of inserted + skipped. Never fails on individual bad rows.

**Q20: What is the lifespan context manager?**
A: FastAPI 0.100+ uses `lifespan` instead of `@app.on_event("startup")`. It's an async generator: code before `yield` runs on startup (init_db), code after runs on shutdown (cleanup).

### 25.3 Frontend Questions (20)

**Q21: How does the AuthContext work?**
A: Creates React Context with state from localStorage. `login()` saves tokens + user info. `logout()` clears localStorage. Provides derived booleans: isAuthenticated, isAdmin, isAnalyst, isViewer. All components access auth state via `useAuth()` hook.

**Q22: How does ProtectedRoute work?**
A: Wraps route content. Checks `isAuthenticated` — if false, redirects to /login. If `roles` prop specified, checks user.role against allowed roles — if not allowed, shows "Access Denied". Otherwise renders children.

**Q23: Explain the Axios interceptor pattern.**
A: Request interceptor: reads JWT from localStorage, attaches as Bearer header. Response interceptor: catches 401 responses, calls onUnauthorized callback (triggers logout + redirect). Enables global auth without modifying each API call.

**Q24: How does the blob download work for reports?**
A: Standard `<a href>` can't send Authorization headers. Solution: Axios fetches the file as a blob (responseType: 'blob') with JWT attached by interceptor. Then creates a temporary object URL, triggers download via programmatic anchor click, cleans up.

**Q25: How is theme toggle implemented?**
A: Topbar component reads/writes `data-theme` attribute on `<html>`. CSS uses `[data-theme="dark"]` selector to override CSS variables. Theme choice persisted in localStorage. All components use CSS variables (var(--bg-primary)) so they auto-adapt.

**Q26: What is the useApi custom hook?**
A: Encapsulates common API call pattern: `const { data, loading, error, execute } = useApi(apiFunction)`. Manages loading state, catches errors, stores response data. Avoids repeating try/catch/loading logic in every page.

**Q27: How does GlobalAuthWatcher work?**
A: A component that registers the `onUnauthorized` callback (from client.js) on mount. When any API call returns 401, this callback fires, calling `logout()` and `navigate('/login')`. Single global handler for expired tokens.

**Q28: How does the forecast progress bar work?**
A: Forecast.jsx shows a progress bar that fills during model training. For single model: 0% → animates to ~80% while waiting → jumps to 100% on response. For compare: fills 33% per model as each completes sequentially.

**Q29: How is the Dashboard data loaded?**
A: On mount, Dashboard.jsx calls multiple endpoints in parallel: `demandTrend()`, `listInventory()`, `categoryBreakdown()`. Uses `useEffect` with `Promise.all` pattern. KPIs are computed from the combined responses.

**Q30: How does CSV export work on Dashboard?**
A: Builds a CSV string from the data grid state, creates a Blob, generates object URL, triggers download via anchor click. Pure client-side — no backend call needed.

### 25.4 Database Questions (10)

**Q31: Why use composite indexes?**
A: `idx_sales_product_date` covers the most common query pattern: "Get sales for product X between dates A and B". Without it, database scans entire sales table (O(n)). With it, uses B-tree lookup (O(log n)).

**Q32: Why is product_id in inventory marked UNIQUE?**
A: Each product has exactly one inventory record. UNIQUE constraint enforces this at the database level. The ORM relationship uses `uselist=False` for the same reason.

**Q33: What does `ondelete="CASCADE"` do?**
A: Database-level cascade deletion. If a product row is deleted, all related sales/forecasts rows are automatically deleted by the database engine (not Python). This is a backup for ORM cascades.

**Q34: Why store metrics (mae, rmse, mape) on every forecast row?**
A: Allows querying "what was the accuracy when this forecast was generated?" without re-computing. Each forecast day for the same run shares the same metrics values — slight denormalization for query convenience.

**Q35: How would you add migrations?**
A: Use Alembic (SQLAlchemy's migration tool): `alembic init alembic`, configure connection, `alembic revision --autogenerate -m "add column"`, `alembic upgrade head`. This project currently uses `create_all()` (no migration support for schema changes).

### 25.5 ML/Algorithm Questions (15)

**Q36: How does Prophet decompose time series?**
A: y(t) = g(t) + s(t) + h(t) + ε where g=trend, s=seasonality (weekly+yearly), h=holidays, ε=noise. Uses a generalized additive model, similar to curve fitting, not traditional ARIMA.

**Q37: What features does XGBoost use?**
A: 16 features: day_of_week, day_of_month, month, week_of_year, is_weekend, trend (linear), lag_1, lag_7, lag_14, lag_28, rolling_mean_7, rolling_std_7, rolling_mean_14, rolling_std_14, rolling_mean_28, rolling_std_28.

**Q38: Why use recursive forecasting?**
A: XGBoost/LSTM need lag features (yesterday's value). For future predictions, yesterday's value doesn't exist yet. Solution: predict day 1, use that prediction as lag for day 2, repeat. Errors accumulate, so shorter horizons are more accurate.

**Q39: What is Z-score normalization?**
A: (x - mean) / std. Transforms data to have mean=0, std=1. LSTM needs this because neural networks work best with small, standardized input values. After prediction, denormalize: y = y_norm × std + mean.

**Q40: What is EarlyStopping?**
A: Keras callback that monitors validation loss. If loss doesn't improve for `patience` epochs (3 in this project), training stops early and restores the best weights. Prevents overfitting and saves computation time.

**Q41: How are confidence intervals calculated?**
A: Prophet: native intervals (yhat_lower, yhat_upper) from posterior distribution. XGBoost: ±1.96 × residual_std (Gaussian approximation). LSTM: ±1.96 × residual_std × normalization_std.

**Q42: Why clip predictions to max(0, value)?**
A: Demand can never be negative. ML models may predict negative values (especially LSTM with normalized data). Clipping to 0 ensures physically meaningful predictions.

**Q43: What is the MODEL_REGISTRY pattern?**
A: A dictionary mapping model names to service modules. All services implement the same `fit_predict(dates, quantities, horizon)` interface. Adding a new model requires: 1) create service, 2) add to registry. No changes to existing code (Open-Closed Principle).

**Q44: Why 80/20 split for Prophet?**
A: 80% for training (model learns patterns), 20% for testing (evaluates accuracy). The test portion simulates future dates. Metrics computed on test set give realistic accuracy estimates.

**Q45: What happens if LSTM has only 40 days of data?**
A: It raises ValueError because LSTM_SEQUENCE_LENGTH (30) + 30 minimum = 60 days required. With only 40 days, the sliding window can't create enough training samples.

**Q46: How does XGBoost handle missing features during recursive forecast?**
A: When building features for future dates, lag values beyond the training data use the model's own predictions (already appended to history DataFrame). Rolling statistics use the extended history including predictions.

**Q47: What's the difference between MAE and RMSE?**
A: MAE treats all errors equally. RMSE squares errors before averaging, so large errors contribute more. If RMSE >> MAE, the model has occasional large errors. RMSE is preferred for optimization because it penalizes outliers.

**Q48: Why does Prophet disable daily_seasonality?**
A: This data has one value per day (daily aggregates). Daily seasonality models intra-day patterns (hourly), which don't exist in daily data. Enabling it would add noise.

**Q49: How is the "best model" selected in compare?**
A: Lowest RMSE wins. RMSE is chosen over MAE because it penalizes large errors more (important for supply chain where big forecast misses cause stockouts).

**Q50: What's the XGBoost learning_rate=0.05?**
A: Controls how much each tree contributes. Lower = more trees needed but better generalization. 0.05 with 500 trees balances accuracy and training speed.

### 25.6 Security Questions (10)

**Q51: How do you prevent SQL injection?**
A: SQLAlchemy ORM uses parameterized queries. User input is never concatenated into SQL strings. The ORM generates: `SELECT * FROM users WHERE username = ?` with the value passed separately.

**Q52: How does rate limiting prevent brute force?**
A: Auth endpoints limited to 10 attempts/minute per IP. After 10 failed logins, attacker must wait 1 minute. At 10 attempts/minute, trying 10,000 passwords takes 1000 minutes (16+ hours).

**Q53: Why use generic login error messages?**
A: "Invalid username or password" doesn't reveal whether the username exists. Specific messages like "User not found" enable user enumeration attacks (discovering valid usernames).

**Q54: What is path traversal and how is it prevented?**
A: Attack: request `/reports/download/1` where report.file_path = `../../etc/passwd`. Prevention: `p.resolve().relative_to(REPORTS_DIR.resolve())` raises ValueError if the resolved path is outside REPORTS_DIR.

**Q55: Why separate access and refresh tokens?**
A: Access tokens (8hr) are sent with every request — short-lived limits damage if stolen. Refresh tokens (7d) are used only to get new access tokens — stored more securely. Different types prevent misuse.

### 25.7 Architecture Questions (15)

**Q56: Why separate routers from services?**
A: Separation of concerns. Routers handle HTTP (request parsing, response formatting, error codes). Services handle business logic (can be reused by different routers, easier to test, no HTTP dependency).

**Q57: Why not put all code in one file?**
A: Single Responsibility Principle. Each file has one job. Benefits: easier to find code, parallel development, smaller diffs in version control, focused testing.

**Q58: What is the middleware execution order?**
A: Outer-to-inner on request, inner-to-outer on response. CORS → Security → RequestId → BodySize → TrustedHost → RateLimit → Handler → (reverse order for response). Like layers of an onion.

**Q59: Why use environment variables for config?**
A: 12-Factor App methodology. Same code, different config per environment. Secrets never in source code. Easy to change without redeployment. Docker/cloud-native friendly.

**Q60: How does the project handle database portability?**
A: SQLAlchemy abstracts the database. Code uses ORM (models, sessions) — never raw SQL. Changing from SQLite to PostgreSQL requires only updating DATABASE_URL env var. No code changes needed.

**Q61-70:** *(Additional architecture, testing, deployment, and optimization questions following the same pattern)*

**Q61: What is the Provider pattern in React?**
A: A component that wraps the app tree, providing shared state via Context. Children access state via hooks (useAuth, useToast). Avoids passing props through many levels (prop drilling).

**Q62: How would you add real-time updates?**
A: Add WebSocket endpoint in FastAPI (`@app.websocket("/ws")`). Frontend connects via native WebSocket API. Server pushes when new forecasts complete or inventory drops below threshold.

**Q63: How would you add automated testing?**
A: Backend: pytest + httpx TestClient. Test each endpoint with valid/invalid inputs. Frontend: Vitest + React Testing Library. Test component rendering and user interactions.

**Q64: What's the difference between SQLAlchemy 1.x and 2.0?**
A: 2.0 uses new query style (`select(Model).where(...)`) but still supports legacy style (`db.query(Model).filter(...)`). This project uses legacy style for readability.

**Q65: How would you implement caching?**
A: Redis with TTL. Cache dashboard/summary (30s), inventory status (60s), seasonal analysis (5min). Invalidate on data changes. Use FastAPI background tasks for cache warming.

---

## Section 26 — Learning Notes (Summary)

### Key Takeaways Per Section

| Section | Most Important Concept |
|---------|----------------------|
| 1. Overview | Three ML models + JWT auth + React dashboard |
| 2. Architecture | Layered: Presentation → API → Business → Data |
| 3. Tech Stack | FastAPI for speed + Pydantic for validation + SQLAlchemy for DB |
| 4. Folder Structure | Routers (controllers) → Services (logic) → Utils (helpers) |
| 5. File Explanation | Each file has exactly ONE responsibility |
| 6. Code Explanation | MODEL_REGISTRY pattern + Dependency Injection |
| 7. Execution Flow | Request → Middleware stack → Auth → Handler → Service → DB → Response |
| 8. Frontend | Context API for state + Axios interceptors for auth |
| 9. Backend | Lifespan → Middleware → Routers → Services → DB |
| 10. Database | 6 tables + composite indexes + cascade deletes |
| 11. API Docs | All endpoints require JWT except login/register |
| 12. Swagger | Custom routes with forced light CSS |
| 13. Auth | bcrypt(12) + JWT(HS256) + RBAC(admin/analyst/viewer) |
| 14. Logic | Safety Stock = Z × σ × √(lead_time) |
| 15. Imports | 24 Python packages + 8 npm packages |
| 16. Config | pydantic-settings from .env with validation |
| 17. Dependencies | Each package serves one purpose |
| 18. Workflow | install.py → run.py → login → forecast |
| 19. Debugging | Check: venv active? backend running? JWT valid? |
| 20. Performance | LSTM is bottleneck; indexes speed up queries |
| 21. Security | 15+ attack vectors prevented |
| 22. Deployment | Docker compose for production |
| 23. Source Map | main.py imports all routers; services share utils |
| 24. Glossary | 40+ terms defined |
| 25. Interview | 65+ questions with answers |

### Best Practices Followed

1. **Separation of Concerns** — Each file does one thing
2. **DRY (Don't Repeat Yourself)** — Shared utils, common base schemas
3. **SOLID Principles** — Open-Closed (MODEL_REGISTRY), Single Responsibility
4. **12-Factor App** — Config in environment, stateless processes
5. **Defense in Depth** — Multiple security layers
6. **Fail Gracefully** — Try/except everywhere, safe defaults
7. **Idempotent Operations** — init_db() safe to call multiple times
8. **Input Validation** — Pydantic schemas validate all external input
9. **Principle of Least Privilege** — Viewers can't write, analysts can't delete
10. **Clean Code** — Descriptive names, docstrings, type hints

### Common Mistakes to Avoid

1. Running without venv activated
2. Not seeding database before first use
3. Using SQLite in production with concurrent users
4. Committing .env with real secrets
5. Forgetting to add new routers to main.py
6. Not handling ML model ImportError (model not installed)
7. Using autoflush=True (unexpected queries)
8. Forgetting db.commit() after writes
9. Not updating CORS_ORIGINS for production
10. Deploying with default admin password

### Final Interview Tips

- Always explain the **WHY**, not just the **WHAT**
- Mention trade-offs: "SQLite is simpler but doesn't scale; PostgreSQL scales but needs setup"
- Show awareness of security: "We prevent X by doing Y"
- Demonstrate depth: "The Safety Stock formula uses Z=1.65 for 95% service level from the normal distribution"
- Connect to real-world: "A stockout of rice flour could cost ₹50,000/day in lost sales"

---

## End of Complete Learning Document

**Total Coverage:**
- 26 sections covering every aspect of the project
- All 50+ files explained
- All functions documented
- All APIs with examples
- All dependencies described
- Complete architecture diagrams (Mermaid)
- 65+ interview questions with answers
- Security, performance, and deployment guides

**For maintenance over the next 5 years:**
- Start with Section 7 (Execution Flow) to understand how everything connects
- Use Section 11 (API Docs) as daily reference
- Refer to Section 19 (Debugging) when things break
- Review Section 21 (Security) before any deployment changes
- Check Section 22 (Deployment) for infrastructure changes

---

*Document generated for: Retail Demand Forecasting System v1.1.0*
*Author: Karan Dhaodiyal | Program: MCA | License: MIT*

