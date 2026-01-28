from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session,joinedload
from app.database import SessionLocal
from app.models import Inventory, ProductVariant
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

    # Manually return a dict with the extra fields
    return {
        "id": inv.id,
        "product_variant_id": inv.product_variant_id,
        "warehouse_id": inv.warehouse_id,
        "quantity": inv.quantity,
        "reorder_level": inv.reorder_level,
        "product_name": inv.product_variant.product.name,  # via relationship
        "warehouse_name": inv.warehouse.name               # via relationship
    }


# ----------------- List Inventory -----------------
@router.get("/", response_model=List[InventoryOut])
def inventory_list(db: Session = Depends(get_db)):
    """
    Fetch all inventory rows where:
    - The inventory has a product variant
    - The product variant has a linked product
    - The inventory has a warehouse
    """
    
    # Query inventory with joins
    inventory_rows = (
        db.query(Inventory)
        .join(Inventory.product_variant)  # inner join → only rows with variant
        .join(ProductVariant.product)      # inner join → only rows with product
        .join(Inventory.warehouse)        # inner join → only rows with warehouse
        .options(
            joinedload(Inventory.product_variant).joinedload(ProductVariant.product),
            joinedload(Inventory.warehouse)
        )
        .all()
    )

    # Build response
    result = [
        InventoryOut(
            id=inv.id,
            product_variant_id=inv.product_variant_id,
            warehouse_id=inv.warehouse_id,
            quantity=inv.quantity,
            reorder_level=inv.reorder_level,
            product_name=inv.product_variant.product.name,
            warehouse_name=inv.warehouse.name
        )
        for inv in inventory_rows
    ]

    return result

