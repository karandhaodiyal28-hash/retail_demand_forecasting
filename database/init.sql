-- ============================================================
-- Retail Demand Forecasting System - PostgreSQL Schema
-- Author: Karan Dhaodiyal
-- Run: psql -U postgres -d retail_forecast -f database/init.sql
-- NOTE: The app also runs on SQLite out-of-the-box. This file
--       is only needed if you set DATABASE_URL=postgresql://...
-- ============================================================

CREATE DATABASE retail_forecast;
\c retail_forecast;

-- Products master
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(256) NOT NULL,
    category VARCHAR(128),
    unit_cost FLOAT DEFAULT 0,
    unit_price FLOAT DEFAULT 0,
    lead_time_days INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- Daily aggregated sales
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sale_date DATE NOT NULL,
    quantity FLOAT DEFAULT 0,
    revenue FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sales_product_date ON sales(product_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);

-- Stored forecast results
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    model_name VARCHAR(64) NOT NULL,  -- prophet | xgboost | lstm
    forecast_date DATE NOT NULL,
    predicted_quantity FLOAT DEFAULT 0,
    lower_bound FLOAT,
    upper_bound FLOAT,
    horizon_days INTEGER DEFAULT 30,
    mae FLOAT,
    rmse FLOAT,
    mape FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_forecasts_product_model_date
    ON forecasts(product_id, model_name, forecast_date);

-- Inventory state + recommendations
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    current_stock FLOAT DEFAULT 0,
    reorder_point FLOAT DEFAULT 0,
    safety_stock FLOAT DEFAULT 0,
    recommended_order_qty FLOAT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Generated report metadata
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(64) NOT NULL,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    params TEXT,
    file_path VARCHAR(512),
    format VARCHAR(16) DEFAULT 'json',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
