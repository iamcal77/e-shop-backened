from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProductCreate(BaseModel):
    name: str = Field(..., example="iPhone 15")
    description: Optional[str] = Field(None, example="Latest Apple phone")
    product_type: str = Field(..., example="physical")  # physical | digital | service
    url: str = Field(..., example="https://example.com/iphone15")
    is_active: bool = True

class ProductVariantCreate(BaseModel):
    sku: str = Field(..., example="IPH15-BLK-128")
    price: float = Field(..., gt=0)
    size: Optional[str] = Field(None, example="128GB")
    color: Optional[str] = Field(None, example="Black")
    is_active: bool = True

class ProductVariantOut(BaseModel):
    id: int
    sku: str
    price: float
    size: Optional[str]
    color: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    product_type: str
    is_active: bool
    url: str
    created_at: datetime
    variants: Optional[List[ProductVariantOut]] = []

    class Config:
        from_attributes = True  # SQLAlchemy → Pydantic

class ProductVariantCreate(BaseModel):
    sku: str = Field(..., example="IPH15-BLK-128")
    price: float = Field(..., gt=0)
    size: Optional[str] = Field(None, example="128GB")
    color: Optional[str] = Field(None, example="Black")
    is_active: bool = True

