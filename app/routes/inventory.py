from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import admin_only
from ..database import SessionLocal
from ..models import Inventory, Product

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/add", dependencies=[Depends(admin_only)])
def add_stock(product_id: int, qty: int, db: Session = Depends(get_db)):

    product = db.get(Product, product_id)
    if not product:
        return {"error": "Product not found"}

    inventory = db.query(Inventory).filter_by(product_id=product_id).first()

    if not inventory:
        inventory = Inventory(product_id=product_id, quantity=qty)
        db.add(inventory)
    else:
        inventory.quantity += qty

    db.commit()

    return {
        "message": "Inventory updated",
        "product_id": product_id,
        "available_stock": inventory.quantity
    }
@router.get("/")
def get_inventory(db: Session = Depends(get_db)):
    # Join Product with Inventory
    results = (
        db.query(
            Product.id,
            Product.name,
            Product.price,
            Product.category,
            Product.sku,
            Product.image_url,
            Inventory.quantity,
            Inventory.reorder_level
        )
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .all()
    )

    # Convert results to list of dicts
    return [
        {
            "id": r.id,
            "name": r.name,
            "price": r.price,
            "category": r.category,
            "sku": r.sku,
            "image_url": r.image_url,
            "stock": r.quantity or 0,
            "reorder_level": r.reorder_level or 5
        }
        for r in results
    ]

