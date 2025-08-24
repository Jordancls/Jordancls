from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Entry, Breakage, Delay, Complaint, Goal


def get_goal_value(db: Session, key: str, default: float) -> float:
    goal = db.query(Goal).filter(Goal.key == key).first()
    return goal.value if goal else default


def kpis_overview(db: Session) -> dict:
    today = date.today()
    start = today - timedelta(days=30)

    production_30d = db.query(func.coalesce(func.sum(Entry.forno_m2), 0.0)).filter(Entry.date >= start).scalar() or 0.0
    orders_30d = db.query(func.coalesce(func.sum(Entry.pedidos_m2), 0.0)).filter(Entry.date >= start).scalar() or 0.0
    loss_30d = db.query(func.coalesce(func.sum(Breakage.qty_m2), 0.0)).filter(Breakage.date >= start).scalar() or 0.0
    delays_count = db.query(func.count(Delay.id)).filter(Delay.date >= start).scalar() or 0
    complaints_count = db.query(func.count(Complaint.id)).filter(Complaint.date >= start).scalar() or 0

    loss_pct = (loss_30d / max(production_30d, 1.0)) * 100.0

    forno_daily_goal = get_goal_value(db, "forno_daily", 1.0)
    utilization_pct = (production_30d / (forno_daily_goal * 30.0)) * 100.0 if forno_daily_goal else 0.0

    goals = {
        "forno_daily": forno_daily_goal,
        "prod_day": get_goal_value(db, "production_day", 0.0),
        "prod_night": get_goal_value(db, "production_night", 0.0),
        "loss_pct": get_goal_value(db, "loss_pct", 0.0),
    }

    return {
        "production_30d_m2": production_30d,
        "orders_30d_m2": orders_30d,
        "loss_30d_m2": loss_30d,
        "loss_pct": loss_pct,
        "delays_count": delays_count,
        "complaints_count": complaints_count,
        "utilization_pct": utilization_pct,
        "goals": goals,
    }
