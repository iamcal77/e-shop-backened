from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Product, ProductVariant, Category, Inventory, Warehouse
from app.deps import admin_only
from app.schemas.product import ProductCreate, ProductOut, ProductVariantCreate
import csv, io

router = APIRouter(prefix="/products", tags=["Products"])

# ----------------- DB -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------- Products -----------------
@router.post("/", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        return {"error": "Product not found"}
    for key, value in data.dict().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        return {"error": "Product not found"}
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

@router.get("/", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# ----------------- Product Variants -----------------
@router.post("/{product_id}/variants", response_model=dict)
def create_variant(product_id: int, data: ProductVariantCreate, db: Session = Depends(get_db)):
    variant = ProductVariant(product_id=product_id, **data.dict())
    db.add(variant)
    db.commit()
    db.refresh(variant)

    print("Variant created:", variant.id)

    warehouses = db.query(Warehouse).all()
    print("Warehouses found:", len(warehouses))

    for wh in warehouses:
        inv = Inventory(
            product_variant_id=variant.id,
            warehouse_id=wh.id,
            quantity=0,
            reorder_level=0
        )
        db.add(inv)
        print(f"Inventory staged for variant {variant.id} in warehouse {wh.id}")

    db.commit()
    print("Inventory committed")

    return {"id": variant.id}



# ----------------- Categories -----------------
@router.post("/categories")
def create_category(name: str, parent_id: int | None = None, db: Session = Depends(get_db)):
    cat = Category(name=name, parent_id=parent_id)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

# ----------------- Bulk Import/Export -----------------
@router.post("/import")
def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = io.StringIO(file.file.read().decode())
    reader = csv.DictReader(content)
    for row in reader:
        product = Product(
            name=row["name"],
            description=row.get("description"),
            product_type=row.get("product_type", "physical")
        )
        db.add(product)
    db.commit()
    return {"message": "Products imported successfully"}

@router.get("/export")
def export_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "type": p.product_type} for p in products]
