from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from api.auth import get_current_user
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("")
async def list_reports(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = ReportService(db)
    return await svc.list_reports()

@router.get("/{id}")
async def get_report(
    id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = ReportService(db)
    try:
        return await svc.get_report_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/generate")
async def generate_report(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    svc = ReportService(db)
    try:
        return await svc.generate_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
