from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    role: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str


class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
