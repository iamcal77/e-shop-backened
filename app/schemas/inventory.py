from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# -----------------
# Input schema for adjusting inventory
# -----------------
class InventoryAdjust(BaseModel):
    product_variant_id: int = Field(..., example=1)
    warehouse_id: int = Field(..., example=1)
    quantity: int = Field(..., example=10)  # can be positive or negative to adjust
    reorder_level: Optional[int] = Field(5, example=5)  # optional, defaults to 5

# -----------------
# Output schema for inventory record
# -----------------
class InventoryOut(BaseModel):
    id: int
    product_variant_id: int
    warehouse_id: int
    quantity: int
    reorder_level: int

    class Config:
        orm_mode = True
