from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# -------------------------
# Address Schemas
# -------------------------
class AddressCreate(BaseModel):
    line1: str
    city: str
    country: str
    is_default: Optional[bool] = False

class AddressOut(AddressCreate):
    id: int

    class Config:
        orm_mode = True

# -------------------------
# User / Customer Schemas
# -------------------------
class SegmentUpdate(BaseModel):
      segment: str

class UserOut(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    loyalty_points: int
    created_at: datetime
    customer_segment: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    addresses: List[AddressOut] = []

    class Config:
        orm_mode = True


