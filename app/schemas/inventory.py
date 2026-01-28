from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InventoryAdjust(BaseModel):
    product_variant_id: int = Field(..., example=1)
    warehouse_id: int = Field(..., example=1)
    quantity: int = Field(..., example=10, description="Quantity to adjust (can be negative)")
    reorder_level: Optional[int] = Field(None, example=5, description="Optional new reorder level")
# Output schema for inventory record
# -----------------
class InventoryOut(BaseModel):
    id: int
    product_variant_id: int
    warehouse_id: int
    quantity: int
    reorder_level: int
    product_name: Optional[str]  # <-- make optional
    warehouse_name: Optional[str]  # <-- make optional

    class Config:
        orm_mode = True
