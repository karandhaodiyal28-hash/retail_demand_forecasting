# Retail Demand Forecasting System

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16-FF6F00?logo=tensorflow&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.1.0-purple)

> An AI/ML-powered demand forecasting and inventory optimization platform for the **Retail & Supply Chain** domain.
>
> **Author:** Karan Dhaodiyal · **Program:** MCA · **Version:** 1.1.0

Combines **Prophet**, **XGBoost**, and **LSTM** time-series models with a secure **FastAPI** backend and a **React** dashboard (with **Light/Dark theme toggle**) to deliver product demand prediction, inventory recommendations, seasonal analysis, sales forecasting, role-based authentication, and report generation.

---

## 1. Features

| Feature | Description |
|---|---|
| **Product Demand Prediction** | Forecast daily demand for any SKU over a 1-365 day horizon using one of three models. |
| **Inventory Recommendations** | Auto-compute reorder points, safety stock (Z=1.65), and recommended order quantities. |
| **Seasonal Analysis** | Detect weekly/monthly patterns, trend direction, and peak demand periods. |
| **Sales Forecasting** | Multi-model comparison with MAE / RMSE / MAPE evaluation. |
| **Executive BI Dashboard** | Filter bar (date range + category), 4 KPI cards (Total Forecasted Demand, Safety-Stock Alerts, Demand Volatility Index, Projected Sales Revenue), a wide *Historical Sales vs Predicted Demand* chart, *Current Inventory vs Reorder Point* bars, a category demand-distribution donut, and a demand/reorder **data grid** with High/Medium/Low risk badges + **Export CSV / PDF**. |
| **Report Generation** | Export forecasts, inventory status, and seasonal analyses as JSON or CSV. |
| **🔐 Secure Authentication** | JWT access + refresh tokens, bcrypt password hashing, role-based access (admin/analyst/viewer). |
| **🛡 Hardened Security** | Security headers (CSP, HSTS, X-Frame-Options), per-IP rate limiting, body-size limits, audit logging. |
| **🎨 Light/Dark Theme** | Sun/Moon toggle in the top bar, localStorage persistence, CSS custom-property system. Dropdowns, charts, inputs, and tooltips adapt seamlessly to both modes — text always visible. |
| **📊 Interactive API Docs** | Full Swagger UI (`/docs`) and ReDoc (`/redoc`) with forced-light CSS to ensure text visibility regardless of browser dark-mode settings. |

---

## 2. Tech Stack

**Backend (Python 3.12):** FastAPI 0.115 · Uvicorn · SQLAlchemy 2.0 · Pydantic v2 + pydantic-settings · python-dotenv · slowapi (per-IP rate limiting)

**Auth / Security:** python-jose (JWT, HS256) · passlib + bcrypt (password hashing) · python-multipart

**ML / Forecasting:** Prophet 1.1.5 (+ cmdstanpy 1.2.4 backend) · XGBoost 2.1.1 · TensorFlow / Keras 2.16 (LSTM) · scikit-learn 1.5.1 · NumPy 1.26 · Pandas 2.2

**Frontend (Node 18+):** React 18 · Vite 5 · Recharts · React Router · Axios · lucide-react icons · Inter font · custom glassmorphism CSS

**Database:** SQLite (default, zero-config) · PostgreSQL via psycopg2-binary (production, optional)

**Testing / Dev:** pytest · httpx

---

## 3. Algorithms & Concepts

### 3.1 Prophet (Meta)
- Additive generalized linear model
- Decomposition: trend + weekly seasonality + yearly seasonality + holidays
- Strength: handles missing data, outliers, strong seasonal effects
- Use case: products with weekly/monthly patterns and ~1+ year history

### 3.2 XGBoost
- Gradient-boosted decision trees (supervised regression)
- Features engineered: lag(1, 7, 14, 28), rolling mean/std, calendar features
- Strength: captures non-linear interactions between lagged features
- Use case: products with rich feature history (≥ 30 days)

### 3.3 LSTM (Deep Learning)
- Long Short-Term Memory recurrent neural network (TensorFlow/Keras)
- Architecture: 50-unit LSTM → 25 Dense (ReLU) → 1 Dense output, trained with Adam + EarlyStopping
- Strength: captures long-range temporal dependencies
- Use case: products with long histories (≥ 90 days)

### 3.4 Forecast Evaluation Metrics
- **MAE** — Mean Absolute Error
- **RMSE** — Root Mean Squared Error
- **MAPE** — Mean Absolute Percentage Error

### 3.5 Inventory Optimization
- **Safety Stock** = Z(95%) × σ(daily demand) × √(lead time)
- **Reorder Point** = avg_daily_demand × lead_time + safety_stock
- **Recommended Order Qty** = expected_demand_over_horizon − current_stock + safety_stock
- **Status:** OK / LOW / REORDER / OVERSTOCK

---

## 4. Quick Start

### 4.1 One-Command Setup

```bash
# 1. Unzip
unzip retail_demand_forecasting.zip
cd retail_demand_forecasting

# 2. Run the auto-installer
python install.py

# 3. Start both backend and frontend
python run.py
```

The installer creates a virtual environment, installs all dependencies, initializes the SQLite database, seeds 20 sample products with ~400 days of sales data, and creates the default admin user.

### 4.2 Default Login

| Field    | Value      |
|----------|------------|
| URL      | http://localhost:5173 |
| Username | `admin`    |
| Password | `Admin@123` |

> ⚠️ Change the default password immediately after the first login (`POST /api/v1/auth/change-password`).

### 4.3 Access Points (all localhost URLs)

| URL | Description |
|---|---|
| http://localhost:5173 | **React dashboard UI** — open this in your browser |
| http://localhost:8000 | FastAPI backend root (returns app name + version JSON) |
| http://localhost:8000/health | Backend health check (`{"status":"ok"}`) |
| http://localhost:8000/docs | Interactive **Swagger UI** — try every endpoint here |
| http://localhost:8000/redoc | ReDoc API documentation |
| http://localhost:8000/openapi.json | Raw OpenAPI 3 schema |
| http://localhost:8000/api/v1 | Base path for all REST endpoints |

**Every backend REST endpoint lives under `http://localhost:8000/api/v1`, e.g.:**

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/login` | Login, returns JWT access + refresh tokens |
| `GET  /api/v1/products` | List products |
| `POST /api/v1/forecast/run` | Run a single-model forecast |
| `POST /api/v1/forecast/compare` | Compare all three models |
| `GET  /api/v1/inventory` | Inventory status + reorder recommendations |
| `GET  /api/v1/dashboard/summary` | Dashboard KPIs |
| `GET  /api/v1/dashboard/demand-trend` | Historical vs predicted demand series |
| `GET  /api/v1/reports/list` | Generated reports |

> The frontend calls the backend through the Vite dev-server proxy: requests to `/api/v1/*` on `:5173` are forwarded to `:8000`. In normal use you only need to open **http://localhost:5173**.

### 4.4 First Forecast

1. Open http://localhost:5173
2. Sign in with the default credentials
3. Go to **Demand Forecast**
4. Pick any product (e.g. *Premium Wheat Flour 5kg*)
5. Choose a model: **Prophet** / **XGBoost** / **LSTM**
6. Set horizon (e.g. 30 days)
7. Click **Run Forecast** — see predictions + MAE / RMSE / MAPE
8. Optionally click **Compare All Models** — each model (Prophet → XGBoost → LSTM) runs in sequence behind a live progress bar, then the best model (lowest RMSE) is highlighted

### 4.5 Running in VS Code (Manual, Step-by-Step)

Prefer to run it yourself in VS Code instead of the one-command launcher?

**Prerequisites:** Python 3.10–3.12, Node.js 18+, and the VS Code *Python* extension.

1. **Open the project** — VS Code → *File → Open Folder…* → select `retail_demand_forecasting`.

2. **Create & activate a virtual environment** (integrated terminal):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1        # Windows PowerShell
   # source .venv/bin/activate          # macOS / Linux
   ```
   Then *Ctrl+Shift+P → Python: Select Interpreter → .venv*.

3. **Install backend dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialise & seed the database** (creates the SQLite DB, 20 products, sample sales, and the `admin` user):
   ```powershell
   python -m backend.seed_data
   ```

5. **Start the backend** (terminal 1):
   ```powershell
   uvicorn backend.main:app --reload --port 8000
   ```
   → API live at http://localhost:8000/docs

6. **Start the frontend** (terminal 2 — use the split-terminal button):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   → UI live at http://localhost:5173

7. **Log in** at http://localhost:5173 with `admin` / `Admin@123`.

> Shortcut: after step 4 you can just run **`python run.py`** from the project root to launch both servers together instead of steps 5–6.

---

## 5. Project Structure

```
retail_demand_forecasting/
├── install.py                      # Auto-installer
├── run.py                          # Main launcher (backend + frontend)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── SECURITY.md                     # Security & vulnerability report
├── .env.example                    # Environment template
├── backend/
│   ├── main.py                     # FastAPI app entrypoint + middleware
│   ├── config.py                   # Pydantic settings
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── models.py                   # ORM models (User, Product, Sale, Forecast, Inventory, Report)
│   ├── schemas.py                  # Pydantic schemas (request/response validation)
│   ├── auth.py                     # bcrypt + JWT helpers + dependencies
│   ├── seed_data.py                # Sample data + default admin
│   ├── generate_sample_csv.py      # Generate CSV for bulk import
│   ├── routers/
│   │   ├── auth.py                 # /api/v1/auth/{login, register, me, refresh, change-password}
│   │   ├── products.py             # /api/v1/products
│   │   ├── sales.py                # /api/v1/sales (+ bulk, import-csv)
│   │   ├── forecast.py             # /api/v1/forecast/{run, compare, history, seasonal, models}
│   │   ├── inventory.py            # /api/v1/inventory
│   │   ├── reports.py              # /api/v1/reports/{generate, download, list}
│   │   └── dashboard.py            # /api/v1/dashboard/{summary, revenue-trend, category-breakdown, demand-trend}
│   ├── services/
│   │   ├── prophet_service.py      # Prophet wrapper
│   │   ├── xgboost_service.py      # XGBoost with lag/rolling features
│   │   ├── lstm_service.py         # LSTM with sliding window
│   │   ├── forecast_service.py     # Orchestration + persistence
│   │   ├── inventory_service.py    # Inventory optimization
│   │   └── report_service.py       # Report generation (JSON/CSV)
│   └── utils/
│       ├── metrics.py              # MAE / RMSE / MAPE
│       └── seasonal.py             # Seasonal decomposition
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/client.js           # Axios + JWT interceptor
│       ├── context/AuthContext.jsx
│       ├── components/
│       │   ├── ProtectedRoute.jsx  # Auth guard
│       │   ├── Sidebar.jsx
│       │   ├── Topbar.jsx          # User menu + breadcrumb + 🌓 Theme Toggle
│       │   ├── ToastContext.jsx    # Toast notifications
│       │   └── useApi.js
│       ├── pages/
│       │   ├── Login.jsx           # 🔐 Glassmorphism login/register
│       │   ├── Dashboard.jsx
│       │   ├── Forecast.jsx
│       │   ├── Inventory.jsx
│       │   ├── Sales.jsx
│       │   ├── Products.jsx
│       │   ├── Seasonal.jsx
│       │   └── Reports.jsx
│       ├── styles/index.css        # Glassmorphism design system
│       └── utils/format.js
├── database/
│   └── init.sql                    # PostgreSQL schema
├── data/                           # SQLite DB, reports (auto-created, gitignored)
├── docs/                           # Architecture / API reference
└── tests/
    └── test_api.py                 # Authenticated smoke tests
```

---

## 6. Configuration

Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/retail_forecast.db` | Use `postgresql://user:pass@host:5432/db` for Postgres |
| `SECRET_KEY` | random per-process | **Set a strong value in production** (e.g. `python -c "import secrets; print(secrets.token_urlsafe(64))"`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 480 | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | 10080 | JWT refresh token lifetime |
| `BCRYPT_ROUNDS` | 12 | Password hashing work factor |
| `CORS_ORIGINS` | `localhost:5173,3000` | Comma-separated allowed origins |
| `RATE_LIMIT_DEFAULT` | 120/minute | Per-IP request rate limit |
| `RATE_LIMIT_AUTH` | 10/minute | Auth endpoint rate limit (anti-brute-force) |
| `RATE_LIMIT_FORECAST` | 10/minute | Forecast endpoint rate limit (LSTM is expensive) |
| `MAX_UPLOAD_BYTES` | 10 MB | Max CSV upload size |
| `MAX_CSV_ROWS` | 200000 | Max rows per CSV import |

### Using PostgreSQL (Optional)

```bash
# 1. Create database
psql -U postgres -f database/init.sql

# 2. Update .env
echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/retail_forecast" > .env

# 3. Re-seed
python -c "from backend.seed_data import seed; seed(force=True)"
```

---

## 7. Security

This release ships with a hardened security baseline. See **[SECURITY.md](SECURITY.md)** for the full vulnerability report and remediations.

Highlights:
- **JWT auth** on all protected endpoints (HS256, configurable secret)
- **bcrypt** password hashing with configurable work factor
- **Role-based access control** (admin / analyst / viewer)
- **Rate limiting** (slowapi) on every endpoint, with separate budgets for auth & forecast
- **Security headers** (CSP, HSTS, X-Frame-Options DENY, X-Content-Type-Options nosniff, Permissions-Policy)
- **Request body size limit** (configurable, default 10 MB)
- **TrustedHost middleware** (defence in depth against host-header attacks)
- **CORS** restricted to a configured allow-list
- **Pydantic validation** on every input (regex check on usernames/SKUs, password policy, numeric bounds)
- **Path-traversal protection** in `/reports/download`
- **CSV import hardening** (content-type check, row cap, malformed-row skip)
- **Generic auth error** to prevent user-enumeration
- **JSON-safe error responses** (no internal tracebacks leaked)
- **Audit fields** on reports (`created_by`)

---

## 8. API Reference (Key Endpoints)

| Method | Endpoint | Auth | Roles |
|---|---|---|---|
| POST | `/api/v1/auth/register` | public | (admin role requires existing admin) |
| POST | `/api/v1/auth/login` | public | (rate-limited 10/min) |
| GET  | `/api/v1/auth/me` | yes | any |
| POST | `/api/v1/auth/refresh` | yes | any |
| POST | `/api/v1/auth/change-password` | yes | any |
| GET  | `/api/v1/products` | yes | any |
| POST | `/api/v1/products` | yes | admin / analyst |
| PUT  | `/api/v1/products/{id}` | yes | admin / analyst |
| DELETE | `/api/v1/products/{id}` | yes | admin |
| POST | `/api/v1/forecast/run` | yes | any (rate-limited 10/min) |
| POST | `/api/v1/forecast/compare` | yes | admin / analyst |
| GET  | `/api/v1/inventory` | yes | any |
| PUT  | `/api/v1/inventory/{id}` | yes | admin / analyst |
| POST | `/api/v1/reports/generate` | yes | admin / analyst |
| GET  | `/api/v1/dashboard/summary` | yes | any |

Full interactive docs at http://localhost:8000/docs

---

## 9. Troubleshooting

**Prophet / TensorFlow install fail?**
- `python install.py --skip-ml` to install core only
- On Windows, install Visual C++ Build Tools first
- On Linux: `sudo apt install -y python3-dev build-essential`

**Frontend doesn't start?**
- Install Node.js 18+ from https://nodejs.org/
- Then: `cd frontend && npm install && npm run dev`

**Forgot admin password?**
- Reset: `python -c "from backend.database import SessionLocal; from backend import models; from backend.auth import hash_password; db=SessionLocal(); u=db.query(models.User).filter_by(username='admin').first(); u.hashed_password=hash_password('Admin@123'); db.commit()"`

**LSTM is slow?**
- Reduce `LSTM_EPOCHS` in `.env`

**Port 8000 already in use?**
- Edit `run.py` and change `--port 8000` to another port

---

## 10. What's New (v1.1.0)

| Change | Details |
|---|---|
| **Light / Dark Mode Toggle** | Sun/Moon icon in the top bar. Theme stored in `localStorage`; no flash on reload thanks to an inline `<script>` in `index.html`. Entire CSS uses custom properties for both palettes. |
| **Authenticated Report Download** | JSON/CSV reports now download via authenticated blob fetch (JWT token attached by axios interceptor) instead of a plain `<a href>` that caused 401 errors. |
| **Swagger UI Text Fix** | Custom `/docs` route with forced `color-scheme: light` CSS prevents browser dark-mode from making Swagger text invisible. |
| **Executive BI Dashboard** | Date-range + category filter bar, 4 KPI cards, demand chart, inventory bars, category donut, data grid with risk badges + CSV export. |
| **Multi-Model Comparison** | Run Prophet → XGBoost → LSTM sequentially with a live progress bar; best model (lowest RMSE) highlighted. |

---

## 11. License

Released under the **MIT License** — see [LICENSE](LICENSE). © 2026 Karan Dhaodiyal, MCA.
