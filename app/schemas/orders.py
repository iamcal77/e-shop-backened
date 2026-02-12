from pydantic import BaseModel
from typing import List

class ReturnItemSchema(BaseModel):
    order_item_id: int
    quantity: int

class ReturnRequestSchema(BaseModel):
    reason: str
    items: List[ReturnItemSchema]