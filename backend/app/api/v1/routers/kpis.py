from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.services.kpi_calculator import kpis_overview
from app.services.report_text import build_executive_text


router = APIRouter()


@router.get("/overview")
def overview(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    kpis = kpis_overview(db)
    kpis["executive_text"] = build_executive_text(kpis)
    return kpis
