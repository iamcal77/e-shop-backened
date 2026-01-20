from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Cart, CartItem, Order, OrderItem, OrderAddress
from app.routes.auth import get_db
from app.schemas.cart import (
    CartItemCreate,
    CartResponse,
    CheckoutRequest,
    OrderResponse
)

router = APIRouter(prefix="/cart", tags=["Cart & Checkout"])

@router.post("/{cart_id}/items", response_model=CartResponse)
def add_to_cart(
    cart_id: int,
    payload: CartItemCreate,
    db: Session = Depends(get_db)
):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")

    item = CartItem(
        cart_id=cart.id,
        product_variant_id=payload.product_variant_id,
        quantity=payload.quantity
    )

    cart.last_activity_at = datetime.utcnow()
    cart.is_abandoned = False

    db.add(item)
    db.commit()
    db.refresh(cart)
    return cart

@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")
    return cart
@router.post("/checkout", response_model=OrderResponse)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db)
):
    cart = db.query(Cart).filter(Cart.id == payload.cart_id).first()
    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty or missing")

    order = Order(
        user_id=cart.user_id,
        guest_email=payload.guest_email,
        source="ONLINE",
        status="CREATED",
        currency=payload.currency
    )
    db.add(order)
    db.flush()

    total = 0
    for item in cart.items:
        price = item.product_variant.price
        total += price * item.quantity

        db.add(OrderItem(
            order_id=order.id,
            product_variant_id=item.product_variant_id,
            quantity=item.quantity,
            price=price
        ))

    order.total = total

    # Save address snapshot
    if payload.line1:
        db.add(OrderAddress(
            order_id=order.id,
            line1=payload.line1,
            city=payload.city,
            country=payload.country
        ))

    db.delete(cart)  # cart cleared after checkout
    db.commit()

    return OrderResponse(
        order_id=order.id,
        status=order.status,
        total=order.total,
        currency=order.currency
    )

@router.post("/abandoned/{cart_id}")
def mark_abandoned(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(404, "Cart not found")

    cart.is_abandoned = True
    db.commit()
    return {"message": "Cart marked as abandoned"}
