from datetime import datetime
from io import StringIO
import csv
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from pydantic import BaseModel
from app.api.v1.deps import require_roles, get_current_user
from app.db.session import get_db
from app.db import models


router = APIRouter()


def parse_date(value: str) -> datetime.date:
    # Accept YYYY-MM-DD or DD/MM/YYYY
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise HTTPException(status_code=400, detail=f"Invalid date format: {value}")


def build_filters(query, model, params: dict[str, Any]):
    if "from" in params and params["from"]:
        query = query.filter(model.date >= parse_date(params["from"]))
    if "to" in params and params["to"]:
        query = query.filter(model.date <= parse_date(params["to"]))
    if model is models.Delay and params.get("customer"):
        query = query.filter(models.Delay.customer.ilike(f"%{params['customer']}%"))
    if model is models.Breakage and params.get("sector"):
        query = query.filter(models.Breakage.sector == params["sector"])
    return query


def apply_pagination_and_sort(query, model, order_by: str | None, is_desc: bool, limit: int, offset: int):
    if order_by:
        column = getattr(model, order_by, None)
        if column is not None:
            query = query.order_by(desc(column) if is_desc else asc(column))
    else:
        query = query.order_by(desc(model.id))
    return query.limit(limit).offset(offset)


class EntryIn(BaseModel):
    date: str
    shift: str
    pedidos_m2: float
    forno_m2: float
    notes: str | None = None


class DelayIn(BaseModel):
    date: str
    order_code: str
    customer: str
    days_late: float
    reason: str
    order_value: float | None = None


class BreakageIn(BaseModel):
    date: str
    sector: str
    type: str
    operator: str | None = None
    qty_m2: float
    notes: str | None = None


class ComplaintIn(BaseModel):
    date: str
    customer: str
    type: str
    qty: float
    description: str | None = None


def create_instance(model, data: dict[str, Any]):
    data = data.copy()
    if "date" in data and isinstance(data["date"], str):
        data["date"] = parse_date(data["date"])  # type: ignore
    return model(**data)


def stream_csv(rows: list[dict[str, Any]]) -> str:
    output = StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def list_endpoint(model):
    def endpoint(
        db: Session = Depends(get_db),
        _user=Depends(get_current_user),
        from_: str | None = Query(None, alias="from"),
        to: str | None = None,
        customer: str | None = None,
        sector: str | None = None,
        order_by: str | None = None,
        desc_: bool = Query(False, alias="desc"),
        limit: int = 100,
        offset: int = 0,
    ):
        params = {"from": from_, "to": to, "customer": customer, "sector": sector}
        query = db.query(model)
        query = build_filters(query, model, params)
        query = apply_pagination_and_sort(query, model, order_by, desc_, limit, offset)
        results = query.all()
        # Serialize to dicts
        payload = []
        for r in results:
            d = {c: getattr(r, c) for c in r.__table__.columns.keys()}
            if isinstance(d.get("date"), (datetime,)):
                d["date"] = d["date"].date().isoformat()
            elif d.get("date"):
                d["date"] = d["date"].isoformat()
            payload.append(d)
        return payload

    return endpoint


def create_endpoint(model, schema_cls):
    def endpoint(payload: schema_cls, db: Session = Depends(get_db), _user=Depends(require_roles("SUPERVISOR", "ADMIN"))):
        instance = create_instance(model, payload.model_dump())
        db.add(instance)
        db.commit()
        db.refresh(instance)
        d = {c: getattr(instance, c) for c in instance.__table__.columns.keys()}
        if d.get("date"):
            d["date"] = d["date"].isoformat()
        return d

    return endpoint


def import_endpoint(model, columns: list[str]):
    async def endpoint(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        _user=Depends(require_roles("SUPERVISOR", "ADMIN")),
    ):
        content = (await file.read()).decode("utf-8")
        reader = csv.DictReader(StringIO(content))
        count = 0
        for row in reader:
            data = {col: row.get(col) for col in columns}
            try:
                # Coerce types
                if "date" in data and data["date"] is not None:
                    data["date"] = parse_date(data["date"])  # type: ignore
                float_fields = {"pedidos_m2", "forno_m2", "days_late", "order_value", "qty_m2", "qty"}
                for f in float_fields:
                    if f in data and data[f] not in (None, ""):
                        data[f] = float(data[f])
                instance = model(**data)
                db.add(instance)
                count += 1
            except Exception as e:  # skip bad lines
                continue
        db.commit()
        return {"inserted": count}

    return endpoint


def export_endpoint(model):
    def endpoint(
        db: Session = Depends(get_db),
        _user=Depends(get_current_user),
        from_: str | None = Query(None, alias="from"),
        to: str | None = None,
        customer: str | None = None,
        sector: str | None = None,
        order_by: str | None = None,
        desc_: bool = Query(False, alias="desc"),
        limit: int = 10000,
        offset: int = 0,
    ):
        params = {"from": from_, "to": to, "customer": customer, "sector": sector}
        query = db.query(model)
        query = build_filters(query, model, params)
        query = apply_pagination_and_sort(query, model, order_by, desc_, limit, offset)
        results = query.all()
        rows: list[dict[str, Any]] = []
        for r in results:
            d = {c: getattr(r, c) for c in r.__table__.columns.keys()}
            if d.get("date"):
                d["date"] = d["date"].isoformat()
            rows.append(d)
        csv_text = stream_csv(rows)
        return Response(content=csv_text, media_type="text/csv")

    return endpoint


# Entries
router.get("/entries")(list_endpoint(models.Entry))
router.post("/entries")(create_endpoint(models.Entry, EntryIn))
router.post("/entries/import")(import_endpoint(models.Entry, ["date", "shift", "pedidos_m2", "forno_m2", "notes"]))
router.get("/entries/export")(export_endpoint(models.Entry))

# Delays
router.get("/delays")(list_endpoint(models.Delay))
router.post("/delays")(create_endpoint(models.Delay, DelayIn))
router.post("/delays/import")(import_endpoint(models.Delay, ["date", "order_code", "customer", "days_late", "reason", "order_value"]))
router.get("/delays/export")(export_endpoint(models.Delay))

# Breakages
router.get("/breakages")(list_endpoint(models.Breakage))
router.post("/breakages")(create_endpoint(models.Breakage, BreakageIn))
router.post("/breakages/import")(import_endpoint(models.Breakage, ["date", "sector", "type", "operator", "qty_m2", "notes"]))
router.get("/breakages/export")(export_endpoint(models.Breakage))

# Complaints
router.get("/complaints")(list_endpoint(models.Complaint))
router.post("/complaints")(create_endpoint(models.Complaint, ComplaintIn))
router.post("/complaints/import")(import_endpoint(models.Complaint, ["date", "customer", "type", "qty", "description"]))
router.get("/complaints/export")(export_endpoint(models.Complaint))
