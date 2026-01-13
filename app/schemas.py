from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)
    role: str = "USER"

class UserLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str | None = None
    category: str | None = None
    sku: str | None = None
    image_url: str | None = None
    is_active: bool = True
    
class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    description: str | None
    category: str | None
    image_url: str | None
    stock: int

    class Config:
        orm_mode = True    
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
