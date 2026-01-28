# app/routers/warehouses.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseOut



router = APIRouter(prefix="/warehouses", tags=["Wherehouses"])

# ----------------- DB -----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/", response_model=WarehouseOut)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db)):
    wh = Warehouse(**data.dict())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh

@router.get("/", response_model=List[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()
