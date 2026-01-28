from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Cart, CartItem, Order, OrderItem, OrderAddress, Inventory, Payment
from app.routes.auth import get_db
from app.schemas.cart import CartItemCreate, CartResponse, CheckoutRequest, OrderResponse

router = APIRouter(prefix="/cart", tags=["Cart & Checkout"])

@router.post("/items", response_model=CartResponse)
def add_to_cart(
    payload: CartItemCreate,
    cart_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Fetch or create cart
    cart = db.query(Cart).filter(Cart.id == cart_id).first() if cart_id else None
    if not cart:
        cart = Cart(
            user_id=None,
            is_abandoned=False,
            last_activity_at=datetime.utcnow()
        )
        db.add(cart)
        db.flush()  # cart.id available

    # Add or update item
    item = db.query(CartItem).filter_by(
        cart_id=cart.id,
        product_variant_id=payload.product_variant_id
    ).first()

    if item:
        item.quantity += payload.quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_variant_id=payload.product_variant_id,
            quantity=payload.quantity
        )
        db.add(item)

    # Update cart metadata
    cart.last_activity_at = datetime.utcnow()
    cart.is_abandoned = False

    db.commit()
    db.refresh(cart)

    # Build response manually
    items_out = []
    for ci in cart.items:
        variant = ci.product_variant
        product = variant.product if variant else None
        items_out.append({
            "id": ci.id,
            "product_variant_id": ci.product_variant_id,
            "quantity": ci.quantity,
            "price": variant.price if variant else 0,
            "name": product.name if product else "Unknown",
            "description": product.description if product else "",
            "url": product.url if product else "",
            "image_url": product.url if product else "",
        })

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "is_abandoned": cart.is_abandoned,
        "items": items_out
    }


@router.post("/checkout", response_model=OrderResponse)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db)):
    # 1️⃣ Fetch the cart
    cart = db.query(Cart).filter(Cart.id == payload.cart_id).first()
    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty or missing")

    # 2️⃣ Create the order
    order = Order(
        user_id=cart.user_id,
        status="CREATED",
        currency=payload.currency
    )
    db.add(order)
    db.flush()  # to get order.id

    total = 0

    # 3️⃣ Process each cart item
    for item in cart.items:
        price = item.product_variant.price
        total += price * item.quantity

        # Create order item
        db.add(OrderItem(
            order_id=order.id,
            product_variant_id=item.product_variant_id,
            quantity=item.quantity,
            price=price
        ))

        # Deduct from inventory (choose warehouse, e.g., first available)
        inv = db.query(Inventory).filter_by(
            product_variant_id=item.product_variant_id,
            warehouse_id=payload.warehouse_id  # frontend should send selected warehouse
        ).first()

        if not inv or inv.quantity < item.quantity:
            raise HTTPException(400, f"Not enough stock for variant {item.product_variant_id}")

        inv.quantity -= item.quantity

        # Optional low-stock alert
        if inv.quantity <= inv.reorder_level:
            print(f"⚠️ Low stock for variant {item.product_variant_id} in warehouse {inv.warehouse_id}")

    order.total = total

    # 4️⃣ Save shipping / address snapshot
    if payload.line1:
        db.add(OrderAddress(
            order_id=order.id,
            line1=payload.line1,
            city=payload.city,
            country=payload.country
        ))

    # 5️⃣ Create payment record
    payment = Payment(
        order_id=order.id,
        provider=payload.payment_provider,  # e.g., "MPESA"
        status="PENDING",
        amount=total
    )
    db.add(payment)

    # 6️⃣ Delete the cart
    db.delete(cart)

    # 7️⃣ Commit all changes
    db.commit()
    db.refresh(order)

    return OrderResponse(
        order_id=order.id,
        status=order.status,
        total=order.total,
        currency=order.currency,
    )

@router.get("/items", response_model=CartResponse)
def get_cart_items(cart_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """
    Fetch all items in a cart by cart_id with full product details.
    """
    if not cart_id:
        raise HTTPException(status_code=400, detail="cart_id is required")

    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Build items with product details
    items_out = []
    for item in cart.items:
        variant = item.product_variant
        if variant:
            product = variant.product
            items_out.append({
                "id": item.id,
                "product_variant_id": item.product_variant_id,
                "quantity": item.quantity,
                "price": variant.price,
                "name": product.name if product else "Unnamed Product",
                "description": product.description if product else "",
                "url": product.url if product else "",
                "image_url": product.url if product else "",  # use an image field if you have one
            })
        else:
            items_out.append({
                "id": item.id,
                "product_variant_id": item.product_variant_id,
                "quantity": item.quantity,
                "price": 0,
                "name": "Unknown",
                "description": "",
                "url": "",
                "image_url": "",
            })

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "is_abandoned": cart.is_abandoned,
        "items": items_out
    }

@router.delete("/items", response_model=CartResponse)
def clear_cart(cart_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """
    Clear all items from a cart.
    """
    if not cart_id:
        raise HTTPException(status_code=400, detail="cart_id is required")

    cart = db.query(Cart).filter(Cart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    # Delete all items in the cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(cart)

    # Return the empty cart
    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "is_abandoned": cart.is_abandoned,
        "items": []
    }
