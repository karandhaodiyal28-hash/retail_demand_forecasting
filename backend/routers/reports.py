"""Report endpoints (auth required)."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user, require_role
from ..services.report_service import (
    generate_forecast_report, generate_inventory_report, generate_seasonal_report,
)
from ..config import REPORTS_DIR


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
def generate(
    payload: schemas.ReportRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin", "analyst")),
):
    try:
        if payload.report_type == "forecast":
            if payload.product_id is None:
                raise HTTPException(400, "product_id required for forecast report")
            return generate_forecast_report(db, payload.product_id, payload.format, user_id=user.id)
        if payload.report_type == "inventory":
            return generate_inventory_report(db, payload.format, user_id=user.id)
        if payload.report_type == "seasonal":
            if payload.product_id is None:
                raise HTTPException(400, "product_id required for seasonal report")
            return generate_seasonal_report(db, payload.product_id, payload.format, user_id=user.id)
        raise HTTPException(400, "Unknown report_type")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/download/{report_id}")
def download(
    report_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    rep = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not rep:
        raise HTTPException(404, "Report not found")
    p = Path(rep.file_path)
    # Path-traversal hardening: ensure file lives inside REPORTS_DIR
    try:
        p.resolve().relative_to(REPORTS_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid report path")
    if not p.exists():
        raise HTTPException(404, "Report file missing on disk")
    return FileResponse(p, filename=p.name)


@router.get("/list")
def list_reports(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    rows = db.query(models.Report).order_by(models.Report.created_at.desc()).limit(50).all()
    return [
        {
            "id": r.id, "report_type": r.report_type, "product_id": r.product_id,
            "format": r.format, "file_path": r.file_path, "created_at": r.created_at,
        }
        for r in rows
    ]
