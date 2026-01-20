from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Discount & Coupon
class DiscountCreate(BaseModel):
    type: str = Field(..., example="percentage")
    value: float = Field(..., gt=0)
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    active: bool = True
    customer_segment: Optional[str]

class CouponCreate(BaseModel):
    code: str
    discount_id: int
    usage_limit: Optional[int] = 1

# Price Rules
class PriceRuleCreate(BaseModel):
    product_variant_id: int
    customer_segment: Optional[str]
    region: Optional[str]
    price: float
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    active: bool = True

# Tax Rules
class TaxRuleCreate(BaseModel):
    region: str
    tax_percentage: float
    active: bool = True
