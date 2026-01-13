from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session,joinedload

from app.deps import cashier_only
from app.schemas import POSSale
from ..database import SessionLocal
from ..models import Product, Inventory, POSOrder, POSOrderItem, User

router = APIRouter(prefix="/pos", tags=["POS"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def deduct_stock(db, product_id, qty):
    inv = db.query(Inventory).filter_by(product_id=product_id).first()
    if inv.quantity < qty:
        raise Exception("Insufficient stock")
    inv.quantity -= qty

@router.post("/sell", dependencies=[Depends(cashier_only)])
def pos_sell(sale: POSSale, db: Session = Depends(get_db)):
    order = POSOrder(
        cashier_id=sale.cashier_id,
        payment_method=sale.payment_method,
        total=0
    )
    db.add(order)
    db.flush()

    total = 0
    for item in sale.items:
        product = db.query(Product).get(item.product_id)

        if not product:
            raise Exception(f"Product {item.product_id} not found")

        deduct_stock(db, product.id, item.quantity)

        db.add(POSOrderItem(
            pos_order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        ))

        total += product.price * item.quantity

    order.total = total
    db.commit()
    return {"message": "Sale successful", "total": total}

@router.get("/")
def get_sales(db: Session = Depends(get_db)):
    orders = db.query(POSOrder).all()
    result = []

    for order in orders:
        items = [
            {
                "product_id": item.product_id,
                "name": item.product.name,
                "price": item.price,
                "quantity": item.quantity,
                "subtotal": item.price * item.quantity
            }
            for item in db.query(POSOrderItem).filter_by(pos_order_id=order.id).all()
        ]

        cashier = db.query(User).get(order.cashier_id)
        result.append({
            "id": order.id,
            "cashier_id": order.cashier_id,
            "cashier_email": cashier.email if cashier else None,
            "total": order.total,
            "payment_method": order.payment_method,
            "created_at": order.created_at,
            "items": items
        })

    return result

