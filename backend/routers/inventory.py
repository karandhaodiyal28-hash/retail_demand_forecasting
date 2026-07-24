"""Inventory endpoints (auth required)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user, require_role
from ..services.inventory_service import (
    compute_inventory_recommendation, get_all_inventory_status,
)


router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=List[dict])
def list_inventory(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return get_all_inventory_status(db)


@router.get("/{product_id}", response_model=schemas.InventoryOut)
def get_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    try:
        return compute_inventory_recommendation(db, product_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{product_id}", response_model=schemas.InventoryOut)
def update_stock(
    product_id: int,
    payload: schemas.InventoryUpdate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin", "analyst")),
):
    if not db.query(models.Product).filter(models.Product.id == product_id).first():
        raise HTTPException(404, "Product not found")
    try:
        return compute_inventory_recommendation(db, product_id, current_stock=payload.current_stock)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/recompute", response_model=schemas.MessageOut)
def recompute_all(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin", "analyst")),
):
    results = get_all_inventory_status(db)
    return schemas.MessageOut(
        message="Inventory recomputed",
        detail=f"{len(results)} products updated",
    )
