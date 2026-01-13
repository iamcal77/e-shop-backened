from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import admin_only
from ..database import SessionLocal
from ..models import Inventory, Product
from ..schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["Products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", dependencies=[Depends(admin_only)])
def create_product(p: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**p.dict())
    db.add(product)
    db.commit()
    return {"message": "Product created successfully", "product_id": product.id}

@router.get("/", response_model=list[ProductOut])
def get_products(db: Session = Depends(get_db)):
    results = (
        db.query(
            Product.id,
            Product.name,
            Product.price,
            Product.description,
            Product.category,
            Product.image_url,
            Inventory.quantity.label("stock")
        )
        .outerjoin(Inventory, Inventory.product_id == Product.id)
        .all()
    )

    # map tuples to dict for Pydantic
    return [
        {
            "id": r.id,
            "name": r.name,
            "price": r.price,
            "description": r.description,
            "category": r.category,
            "image_url": r.image_url,
            "stock": r.stock or 0
        }
        for r in results
    ]

