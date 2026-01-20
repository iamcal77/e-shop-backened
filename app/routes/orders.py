from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Order, OrderItem, Payment
from app.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/")
def create_order(data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = Order(user_id=user.id, source="ONLINE")
    db.add(order)
    db.flush()

    total = 0
    for item in data["items"]:
        oi = OrderItem(order_id=order.id, **item)
        total += oi.price * oi.quantity
        db.add(oi)

    order.total = total
    db.commit()
    return {"order_id": order.id, "total": total}

@router.get("/")
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()
