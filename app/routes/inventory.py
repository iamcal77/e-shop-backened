from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Inventory
from app.schemas.inventory import InventoryAdjust, InventoryOut
from app.deps import admin_only
from typing import List

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- Adjust Inventory -----------------
@router.post("/adjust", response_model=InventoryOut)
def adjust_inventory(data: InventoryAdjust, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter_by(
        product_variant_id=data.product_variant_id,
        warehouse_id=data.warehouse_id
    ).first()

    if not inv:
        inv = Inventory(**data.dict())
        db.add(inv)
    else:
        inv.quantity += data.quantity
        if data.reorder_level is not None:
            inv.reorder_level = data.reorder_level

    db.commit()
    db.refresh(inv)

    # Low-stock alert
    if inv.quantity <= inv.reorder_level:
        print(f"⚠️ Low stock alert for variant {inv.product_variant_id} in warehouse {inv.warehouse_id}")

    return inv

# ----------------- List Inventory -----------------
@router.get("/", response_model=List[InventoryOut])
def inventory_list(db: Session = Depends(get_db)):
    return db.query(Inventory).all()
