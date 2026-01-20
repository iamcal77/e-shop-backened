from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)
    role: str = "USER"

class UserLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)

class CartItemCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int


class POSItem(BaseModel):
    product_id: int
    quantity: int

class POSSale(BaseModel):
    cashier_id: int
    payment_method: str
    items: list[POSItem]
