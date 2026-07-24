"""Sales endpoints: list, create, bulk-import.  All require authentication."""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user, require_role
from ..config import settings


router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=List[schemas.SaleOut])
def list_sales(
    product_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    limit = max(1, min(limit, 5000))
    q = db.query(models.Sale)
    if product_id:
        q = q.filter(models.Sale.product_id == product_id)
    if start:
        q = q.filter(models.Sale.sale_date >= start)
    if end:
        q = q.filter(models.Sale.sale_date <= end)
    return q.order_by(models.Sale.sale_date.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=schemas.SaleOut, status_code=201)
def create_sale(
    payload: schemas.SaleCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin", "analyst")),
):
    if not db.query(models.Product).filter(models.Product.id == payload.product_id).first():
        raise HTTPException(404, "Product not found")
    s = models.Sale(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.post("/bulk", response_model=schemas.MessageOut)
def bulk_create(
    payload: schemas.SalesBulkIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin", "analyst")),
):
    if len(payload.sales) > settings.MAX_CSV_ROWS:
        raise HTTPException(413, f"Too many rows (>{settings.MAX_CSV_ROWS})")
    valid_pids = {p.id for p in db.query(models.Product).all()}
    objs = []
    for s in payload.sales:
        if s.product_id not in valid_pids:
            continue
        objs.append(models.Sale(**s.model_dump()))
    db.bulk_save_objects(objs)
    db.commit()
    return schemas.MessageOut(message="Bulk inserted", detail=f"{len(objs)} sales rows")


@router.post("/import-csv", response_model=schemas.MessageOut)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_role("admin", "analyst")),
):
    """CSV format: sku,sale_date,quantity,revenue  (header required)

    Hardened against:
      * oversize uploads (BodySizeLimitMiddleware + checks below)
      * wrong content types
      * pathological CSVs (row cap)
    """
    if file.content_type and file.content_type not in {"text/csv", "application/vnd.ms-excel", "application/octet-stream", "text/plain"}:
        raise HTTPException(415, f"Unsupported content type: {file.content_type}")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large (>{settings.MAX_UPLOAD_BYTES} bytes)")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "File must be UTF-8 encoded")
    reader = csv.DictReader(io.StringIO(text))
    required = {"sku", "sale_date", "quantity"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(400, f"CSV missing required headers: {sorted(required)}")

    sku_to_pid = {p.sku: p.id for p in db.query(models.Product).all()}
    objs = []
    skipped = 0
    for i, row in enumerate(reader):
        if i >= settings.MAX_CSV_ROWS:
            break
        sku = (row.get("sku") or "").strip()
        if sku not in sku_to_pid:
            skipped += 1
            continue
        try:
            objs.append(models.Sale(
                product_id=sku_to_pid[sku],
                sale_date=row["sale_date"],
                quantity=float(row["quantity"]),
                revenue=float(row.get("revenue") or 0),
            ))
        except (ValueError, TypeError, KeyError):
            skipped += 1
    if objs:
        db.bulk_save_objects(objs)
        db.commit()
    return schemas.MessageOut(
        message="CSV import done",
        detail=f"inserted={len(objs)} skipped={skipped}",
    )
