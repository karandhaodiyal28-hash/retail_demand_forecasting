# API Reference

> Full interactive docs: http://localhost:8000/docs

## Authentication

All endpoints (except `POST /api/v1/auth/login` and `POST /api/v1/auth/register`) require a JWT bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

### `POST /api/v1/auth/login`

OAuth2 password flow.  Returns access + refresh tokens.

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=Admin@123
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": { "id": 1, "username": "admin", "role": "admin", "...": "..." }
}
```

**Errors:**
- `401` — invalid credentials (same message for wrong user / wrong password)

### `POST /api/v1/auth/register`

```json
{
  "username": "karan",
  "password": "Strong@123",
  "email": "[email protected]",
  "full_name": "Karan D",
  "role": "analyst"
}
```

Role must be one of `admin | analyst | viewer`.  Self-registration as `admin` is allowed only if no admin exists yet.

### `POST /api/v1/auth/refresh`

```http
POST /api/v1/auth/refresh?refresh_token=<token>
```

### `GET /api/v1/auth/me`

Returns the current user.  Requires auth.

### `POST /api/v1/auth/change-password`

```http
POST /api/v1/auth/change-password?old_password=OldPass1&new_password=NewPass2
```

## Products

| Method | Path | Roles |
|---|---|---|
| GET    | `/api/v1/products?skip=0&limit=100` | any |
| POST   | `/api/v1/products` | admin, analyst |
| GET    | `/api/v1/products/{id}` | any |
| PUT    | `/api/v1/products/{id}` | admin, analyst |
| DELETE | `/api/v1/products/{id}` | admin |

## Sales

| Method | Path | Roles |
|---|---|---|
| GET    | `/api/v1/sales?product_id=&start=&end=&skip=&limit=` | any |
| POST   | `/api/v1/sales` | admin, analyst |
| POST   | `/api/v1/sales/bulk` | admin, analyst |
| POST   | `/api/v1/sales/import-csv` (multipart) | admin, analyst |

## Forecast

| Method | Path | Roles | Rate limit |
|---|---|---|---|
| POST | `/api/v1/forecast/run` | any | 10/min |
| POST | `/api/v1/forecast/compare` | admin, analyst | 10/min |
| GET  | `/api/v1/forecast/history/{product_id}` | any | default |
| GET  | `/api/v1/forecast/seasonal/{product_id}` | any | default |
| GET  | `/api/v1/forecast/models` | any | default |

**Run request:**
```json
{ "product_id": 1, "model_name": "prophet", "horizon_days": 30 }
```

**Response:**
```json
{
  "product_id": 1,
  "model_name": "prophet",
  "horizon_days": 30,
  "metrics": { "mae": 2.1, "rmse": 3.0, "mape": 5.4 },
  "total_predicted": 1234.5,
  "forecasts": [
    { "forecast_date": "2025-01-01", "predicted_quantity": 41.2, "lower_bound": 35.0, "upper_bound": 47.0 },
    "..."
  ]
}
```

## Inventory

| Method | Path | Roles |
|---|---|---|
| GET    | `/api/v1/inventory` | any |
| GET    | `/api/v1/inventory/{product_id}` | any |
| PUT    | `/api/v1/inventory/{product_id}` | admin, analyst |
| POST   | `/api/v1/inventory/recompute` | admin, analyst |

## Reports

| Method | Path | Roles |
|---|---|---|
| POST | `/api/v1/reports/generate` | admin, analyst |
| GET  | `/api/v1/reports/download/{id}` | any |
| GET  | `/api/v1/reports/list` | any |

**Generate request:**
```json
{ "report_type": "forecast", "product_id": 1, "format": "json" }
```

`report_type` ∈ {`forecast`, `inventory`, `seasonal`}, `format` ∈ {`json`, `csv`}.

## Dashboard

| Method | Path | Roles |
|---|---|---|
| GET | `/api/v1/dashboard/summary` | any |
| GET | `/api/v1/dashboard/revenue-trend?days=30` | any |
| GET | `/api/v1/dashboard/category-breakdown` | any |
