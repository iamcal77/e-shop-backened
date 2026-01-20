from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Order, OrderItem
from app.deps import cashier_only

router = APIRouter(prefix="/pos", tags=["POS"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/sell", dependencies=[Depends(cashier_only)])
def pos_sell(data: dict, db: Session = Depends(get_db)):
    order = Order(source="POS", status="PAID")
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
def pos_sales(db: Session = Depends(get_db)):
    return db.query(Order).filter_by(source="POS").all()
