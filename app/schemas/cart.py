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
    price: float           # variant price
    name: str              # product name
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


# -------------------------
# Cart
# -------------------------
class CartResponse(BaseModel):
    id: int
    user_id: Optional[int]
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
    line1: Optional[str] = None           # guest checkout
    city: Optional[str] = None
    country: Optional[str] = None
    payment_provider: str                # MPESA | STRIPE
    currency: str = "KES"
    guest_email: Optional[EmailStr] = None
    warehouse_id: Optional[int] = None


class OrderResponse(BaseModel):
    order_id: int
    status: str
    total: float
    currency: str
