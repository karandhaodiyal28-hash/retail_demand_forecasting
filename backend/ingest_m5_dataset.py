'''Walmart M5 Dataset Ingestion Script

This script processes the Walmart M5 dataset and seeds the database with real retail sales data.

To use this script:
1. Download the M5 dataset from Kaggle: https://www.kaggle.com/c/m5-forecasting-accuracy/data
2. Extract the files to a directory (e.g., 'm5_data')
3. Run this script: python -m backend.ingest_m5_dataset

The script will:
- Create products from items.csv
- Create sales records from sales_train_evaluation.csv
- Map the data to our existing schema
'''
from __future__ import annotations
import csv
import os
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
from typing import List, Tuple, Dict, Any

from sqlalchemy.orm import Session

from .database import SessionLocal, init_db
from . import models
from .auth import hash_password


def load_m5_data(m5_data_dir: str = "m5_data") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load M5 dataset files from the specified directory."""
    m5_path = Path(m5_data_dir)
    
    # Load the main datasets
    sales_df = pd.read_csv(m5_path / "sales_train_evaluation.csv")
    items_df = pd.read_csv(m5_path / "items.csv")
    calendar_df = pd.read_csv(m5_path / "calendar.csv")
    
    return sales_df, items_df, calendar_df


def create_products_from_items(items_df: pd.DataFrame) -> List[Tuple[str, str, str, float, float, int]]:
    """Create product tuples from items.csv data."""
    products = []
    
    # The M5 dataset doesn't have cost/price information, so we'll estimate based on item category
    # Using approximate price ranges for different categories
    category_prices = {
        "FOODS": (10.0, 50.0),
        "HOBBIES": (5.0, 100.0),
        "HOUSEHOLD": (10.0, 200.0)
    }
    
    for _, row in items_df.iterrows():
        # Create SKU from item_id and dept_id
        sku = f"M5-{row['item_id']}-{row['dept_id']}"
        name = row['item_id']  # Use item_id as name since we don't have real names
        category = row['cat_id'] if 'cat_id' in row else 'UNKNOWN'
        
        # Estimate price based on category
        min_price, max_price = category_prices.get(category, (5.0, 50.0))
        price = round(min_price + (max_price - min_price) * 0.6, 2)  # 60% of range
        cost = round(price * 0.7, 2)  # Assume 30% margin
        
        # Lead time based on category
        lead_time = 3 if category == "FOODS" else 5 if category == "HOUSEHOLD" else 7
        
        products.append((sku, name, category, cost, price, lead_time))
    
    return products


def create_sales_from_m5(sales_df: pd.DataFrame, items_df: pd.DataFrame, 
                         calendar_df: pd.DataFrame, 
                         product_mapping: Dict[str, int]) -> List[Dict[str, Any]]:
    """Create sales records from M5 sales data."""
    sales_records = []
    
    # Get date columns (d_1, d_2, ..., d_1941)
    date_columns = [col for col in sales_df.columns if col.startswith('d_')]
    
    # Map day numbers to actual dates using calendar.csv
    # The M5 dataset uses d_1 = 2011-01-29
    base_date = date(2011, 1, 29)
    
    # Create a mapping from day number to date
    day_to_date = {}
    for i, day_col in enumerate(date_columns, 1):
        day_to_date[day_col] = base_date + timedelta(days=i-1)
    
    # Process each row in sales_df
    for _, row in sales_df.iterrows():
        item_id = row['item_id']
        store_id = row['store_id']
        
        # Get product_id from item_id
        if item_id not in product_mapping:
            continue
        
        product_id = product_mapping[item_id]
        
        # Process each day column
        for day_col in date_columns:
            qty = row[day_col]
            if pd.isna(qty) or qty <= 0:
                continue
            
            sale_date = day_to_date[day_col]
            revenue = round(qty * 10.0, 2)  # Estimate revenue (we don't have real prices)
            
            sales_records.append({
                'product_id': product_id,
                'sale_date': sale_date,
                'quantity': float(qty),
                'revenue': revenue
            })
    
    return sales_records


def ingest_m5_dataset(m5_data_dir: str = "m5_data", force: bool = False) -> None:
    """Ingest the M5 dataset into the database."""
    init_db()
    db: Session = SessionLocal()
    
    try:
        print("Loading M5 dataset...")
        sales_df, items_df, calendar_df = load_m5_data(m5_data_dir)
        
        print(f"Loaded {len(sales_df)} sales records, {len(items_df)} items")
        
        # Create products
        print("Creating products from items.csv...")
        products = create_products_from_items(items_df)
        
        # Create product mapping
        product_mapping = {}
        
        # Insert products
        for sku, name, category, cost, price, lead in products:
            # Check if product already exists
            existing = db.query(models.Product).filter(models.Product.sku == sku).first()
            if existing:
                product_mapping[name] = existing.id
                continue
            
            p = models.Product(
                sku=sku, 
                name=name, 
                category=category,
                unit_cost=cost, 
                unit_price=price, 
                lead_time_days=lead,
            )
            db.add(p)
            db.flush()  # Get the ID without committing
            product_mapping[name] = p.id
        
        db.commit()
        print(f"Inserted {len(products)} products")
        
        # Create sales records
        print("Creating sales records from sales data...")
        sales_records = create_sales_from_m5(sales_df, items_df, calendar_df, product_mapping)
        
        # Insert sales records in batches to avoid memory issues
        batch_size = 1000
        for i in range(0, len(sales_records), batch_size):
            batch = sales_records[i:i+batch_size]
            for record in batch:
                db.add(models.Sale(**record))
            db.commit()
            print(f"Inserted batch {i//batch_size + 1} of {len(sales_records)//batch_size + 1}")
        
        print(f"Inserted {len(sales_records)} sales records")
        
        # Create default admin user if not exists
        if not db.query(models.User).filter(models.User.username == "admin").first():
            db.add(models.User(
                username="admin",
                email="[email protected]",
                full_name="Default Admin",
                hashed_password=hash_password("Admin@123"),
                role="admin",
                is_active=1,
            ))
            db.commit()
            print("Created default admin user (username=admin password=Admin@123)")
            
    except Exception as e:
        db.rollback()
        print(f"Error ingesting M5 dataset: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    m5_dir = "m5_data"
    force = False
    
    for arg in sys.argv[1:]:
        if arg.startswith("--dir="):
            m5_dir = arg.split("=", 1)[1]
        elif arg == "--force":
            force = True
    
    print(f"Ingesting M5 dataset from {m5_dir}...")
    ingest_m5_dataset(m5_dir, force)
