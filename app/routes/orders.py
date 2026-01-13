from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import CartItem, Order, Product

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/checkout/{user_id}")
def checkout(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(CartItem).filter_by(user_id=user_id).all()
    total = sum(
        db.query(Product).get(i.product_id).price * i.quantity
        for i in cart
    )
    order = Order(user_id=user_id, total=total)
    db.add(order)
    db.query(CartItem).filter_by(user_id=user_id).delete()
    db.commit()
    return {"order_id": order.id, "total": total}
