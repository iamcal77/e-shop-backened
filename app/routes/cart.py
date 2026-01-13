from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import CartItem

router = APIRouter(prefix="/cart", tags=["Cart"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/add")
def add_to_cart(user_id: int, product_id: int, qty: int, db: Session = Depends(get_db)):
    item = CartItem(user_id=user_id, product_id=product_id, quantity=qty)
    db.add(item)
    db.commit()
    return {"message": "Added to cart"}

@router.get("/{user_id}")
def view_cart(user_id: int, db: Session = Depends(get_db)):
    return db.query(CartItem).filter_by(user_id=user_id).all()
