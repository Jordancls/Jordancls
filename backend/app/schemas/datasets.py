from pydantic import BaseModel


class Entry(BaseModel):
    date: str
    shift: str
    pedidos_m2: float
    forno_m2: float
    notes: str | None = None

    class Config:
        from_attributes = True


class Delay(BaseModel):
    date: str
    order_code: str
    customer: str
    days_late: float
    reason: str
    order_value: float | None = None

    class Config:
        from_attributes = True


class Breakage(BaseModel):
    date: str
    sector: str
    type: str
    operator: str | None = None
    qty_m2: float
    notes: str | None = None

    class Config:
        from_attributes = True


class Complaint(BaseModel):
    date: str
    customer: str
    type: str
    qty: float
    description: str | None = None

    class Config:
        from_attributes = True
