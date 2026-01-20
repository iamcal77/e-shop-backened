from pydantic import BaseModel, EmailStr
from typing import List, Optional


# -------------------------
# Cart Item
# -------------------------
class CartItemCreate(BaseModel):
    product_variant_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: int
    product_variant_id: int
    quantity: int

    class Config:
        from_attributes = True


# -------------------------
# Cart
# -------------------------
class CartResponse(BaseModel):
    id: int
    user_id: Optional[int]
    guest_email: Optional[EmailStr]
    is_abandoned: bool
    items: List[CartItemResponse]

    class Config:
        from_attributes = True


# -------------------------
# Checkout
# -------------------------
class CheckoutRequest(BaseModel):
    cart_id: int
    address_id: Optional[int] = None     # logged-in user
    guest_email: Optional[EmailStr] = None
    line1: Optional[str] = None           # guest checkout
    city: Optional[str] = None
    country: Optional[str] = None
    payment_provider: str                # MPESA | STRIPE
    currency: str = "KES"


class OrderResponse(BaseModel):
    order_id: int
    status: str
    total: float
    currency: str
