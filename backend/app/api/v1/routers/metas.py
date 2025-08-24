from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.v1.deps import require_roles, get_current_user
from app.db.session import get_db
from app.db.models import Goal


router = APIRouter()


class GoalIn(BaseModel):
    key: str
    value: float
    unit: str


@router.get("/")
def list_goals(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    goals = db.query(Goal).order_by(Goal.key).all()
    return [{"id": g.id, "key": g.key, "value": g.value, "unit": g.unit} for g in goals]


@router.post("/", dependencies=[Depends(require_roles("ADMIN"))])
def upsert_goal(payload: GoalIn, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.key == payload.key).first()
    if goal:
        goal.value = payload.value
        goal.unit = payload.unit
    else:
        goal = Goal(key=payload.key, value=payload.value, unit=payload.unit)
        db.add(goal)
    db.commit()
    db.refresh(goal)
    return {"id": goal.id, "key": goal.key, "value": goal.value, "unit": goal.unit}
