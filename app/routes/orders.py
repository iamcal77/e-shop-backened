import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session,joinedload
from fastapi.responses import FileResponse

from app.constants.order_status import OrderStatus
from app.database import SessionLocal
from app.models import Inventory, Order, OrderItem, Payment, ProductVariant, ReturnItem, ReturnRequest, Shipment, ShipmentItem, User
from app.deps import admin_only, get_current_user
from app.schemas.orders import ReturnRequestSchema
from app.services.invoice_service import generate_invoice_pdf
from app.services.order_lifecycle import can_transition

router = APIRouter(prefix="/orders", tags=["Orders"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.post("/")
def create_order(data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = Order(
    user_id=user.id,
    source="ONLINE",
    status=OrderStatus.CREATED
)

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

@router.post("/{order_id}/status")
def update_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if not can_transition(order.status, new_status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status} to {new_status}"
        )

    order.status = new_status
    db.commit()

    return {
        "message": "Order status updated",
        "new_status": order.status
    }

@router.post("/{order_id}/ship")
def create_shipment(
    order_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    """
    data = {
        "warehouse_id": 1,
        "carrier": "DHL",
        "tracking_number": "ABC123",
        "items": [
            {"order_item_id": 1, "quantity": 2}
        ]
    }
    """

    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in [OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.PARTIALLY_SHIPPED]:
        raise HTTPException(status_code=400, detail="Order not ready for shipment")

    shipment = Shipment(
        order_id=order.id,
        warehouse_id=data["warehouse_id"],
        carrier=data["carrier"],
        tracking_number=data["tracking_number"],
        status="SHIPPED"
    )

    db.add(shipment)
    db.flush()

    all_shipped = True

    for item_data in data["items"]:
        order_item = db.query(OrderItem).get(item_data["order_item_id"])

        if not order_item:
            raise HTTPException(status_code=404, detail="Order item not found")

        if order_item.quantity - order_item.shipped_quantity < item_data["quantity"]:
            raise HTTPException(status_code=400, detail="Shipping more than remaining quantity")

        # Deduct inventory
        inventory = db.query(Inventory).filter_by(
            product_variant_id=order_item.product_variant_id,
            warehouse_id=data["warehouse_id"]
        ).first()

        if not inventory or inventory.quantity < item_data["quantity"]:
            raise HTTPException(status_code=400, detail="Insufficient inventory")

        inventory.quantity -= item_data["quantity"]

        # Update shipped quantity
        order_item.shipped_quantity += item_data["quantity"]

        shipment_item = ShipmentItem(
            shipment_id=shipment.id,
            order_item_id=order_item.id,
            quantity=item_data["quantity"]
        )

        db.add(shipment_item)

        if order_item.shipped_quantity < order_item.quantity:
            all_shipped = False

    # Update order status
    order.status = (
        OrderStatus.SHIPPED if all_shipped
        else OrderStatus.PARTIALLY_SHIPPED
    )

    db.commit()

    return {
        "message": "Shipment created",
        "order_status": order.status,
        "shipment_id": shipment.id
    }

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 🚫 Prevent cancelling shipped or partially shipped orders
    if order.status in [
        OrderStatus.PARTIALLY_SHIPPED,
        OrderStatus.SHIPPED,
        OrderStatus.COMPLETED
    ]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel shipped or completed order"
        )

    # Reverse inventory only if order was PAID or PROCESSING
    if order.status in [OrderStatus.PAID, OrderStatus.PROCESSING]:

        for item in order.items:
            # Restore inventory only if some quantity was shipped
            if item.shipped_quantity > 0:

                # Find shipments for this order
                for shipment in order.shipments:
                    for shipment_item in shipment.items:
                        if shipment_item.order_item_id == item.id:

                            inventory = db.query(Inventory).filter_by(
                                product_variant_id=item.product_variant_id,
                                warehouse_id=shipment.warehouse_id
                            ).first()

                            if inventory:
                                inventory.quantity += shipment_item.quantity

    # Mark order cancelled
    order.status = OrderStatus.CANCELLED

    # Trigger refund if payment was successful
    if order.payment and order.payment.status == "SUCCESS":

        order.payment.status = "REFUNDED"
        order.status = OrderStatus.REFUNDED


    db.commit()

    return {
        "message": "Order cancelled successfully",
        "status": order.status
    }

@router.post("/{order_id}/return")
def create_return_request(
    order_id: int,
    data: ReturnRequestSchema,
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed orders can be returned")

    return_request = ReturnRequest(
        order_id=order.id,
        reason=data.reason
    )
    db.add(return_request)
    db.flush()

    for item_data in data.items:
        order_item = db.query(OrderItem).get(item_data.order_item_id)
        if not order_item:
            raise HTTPException(status_code=404, detail="Order item not found")
        if item_data.quantity > order_item.quantity:
            raise HTTPException(status_code=400, detail="Invalid return quantity")

        ri = ReturnItem(
            return_request_id=return_request.id,
            order_item_id=order_item.id,
            quantity=item_data.quantity
        )
        db.add(ri)

    db.commit()

    return {
        "message": "Return request submitted",
        "return_id": return_request.id,
        "status": return_request.status
    }

@router.post("/returns/{return_id}/approve")
def approve_return(
    return_id: int,
    db: Session = Depends(get_db)
):
    return_request = db.query(ReturnRequest).get(return_id)

    if not return_request:
        raise HTTPException(status_code=404, detail="Return not found")

    if return_request.status != "REQUESTED":
        raise HTTPException(status_code=400, detail="Return already processed")

    order = return_request.order

    total_refund = 0

    for item in return_request.items:
        order_item = item.order_item

        # Find shipment warehouse
        for shipment in order.shipments:
            for shipment_item in shipment.items:
                if shipment_item.order_item_id == order_item.id:

                    inventory = db.query(Inventory).filter_by(
                        product_variant_id=order_item.product_variant_id,
                        warehouse_id=shipment.warehouse_id
                    ).first()

                    if inventory:
                        inventory.quantity += item.quantity

        total_refund += order_item.price * item.quantity

    # Update payment
    if order.payment and order.payment.status == "SUCCESS":
        order.payment.status = "REFUNDED"

    return_request.status = "COMPLETED"

    db.commit()

    return {
        "message": "Return approved & refund processed",
        "refund_amount": total_refund
    }

@router.get("/{order_id}/invoice")
def download_invoice(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
      ):

    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Create invoices directory
    os.makedirs("invoices", exist_ok=True)

    file_path = f"invoices/invoice_{order.id}.pdf"

    generate_invoice_pdf(order, file_path)

    return FileResponse(
        path=file_path,
        filename=f"invoice_{order.id}.pdf",
        media_type="application/pdf"
    )

@router.get("/me")
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)  # Now a full User object
):
    orders = db.query(Order).filter(Order.user_id == user.id).all()
    return orders

@router.get("/returns")
def list_all_returns(db: Session = Depends(get_db), user=Depends(admin_only)):
    """
    List all return requests with their items and product names.
    Only accessible by admins.
    """
    return_requests = (
        db.query(ReturnRequest)
        .options(
            joinedload(ReturnRequest.items)
            .joinedload(ReturnItem.order_item)
            .joinedload(OrderItem.product_variant)
            .joinedload(ProductVariant.product)
        )
        .all()
    )

    result = []
    for rr in return_requests:
        rr_dict = {
            "return_id": rr.id,
            "order_id": rr.order_id,
            "reason": rr.reason,
            "status": rr.status,
            "items": []
        }

        for item in rr.items:
            oi = item.order_item
            rr_dict["items"].append({
                "order_item_id": oi.id if oi else None,
                "product_variant_id": oi.product_variant_id if oi else None,
                "product_name": (
                    oi.product_variant.product.name
                    if oi and oi.product_variant and oi.product_variant.product
                    else None
                ),
                "quantity": item.quantity
            })

        result.append(rr_dict)

    return result
@router.get("/{order_id}")
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).options(
        joinedload(Order.items)
        .joinedload(OrderItem.product_variant)
        .joinedload(ProductVariant.product),
        joinedload(Order.shipments)
        .joinedload(Shipment.items)
    ).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order

@router.get("/")
def list_all_orders(
    db: Session = Depends(get_db),
    user: User = Depends(admin_only)
):
    # Fetch all orders with items and shipments
    orders = db.query(Order).options(
        joinedload(Order.items)  # load order items
        .joinedload(OrderItem.product_variant)  # load product variant for each item
        .joinedload(ProductVariant.product),    # load product details
        joinedload(Order.shipments)             # load shipments
        .joinedload(Shipment.items)             # shipment items
    ).all()

    result = []

    for order in orders:
        order_dict = {
            "id": order.id,
            "status": order.status,
            "total": order.total,
            "currency": order.currency,
            "shipping_cost": order.shipping_cost,
            "created_at": order.created_at,
            "source": order.source,
            "user_id": order.user_id,
            "guest_email": order.guest_email,
            "items": [],
            "shipments": []
        }

        # Include order items
        for item in order.items:
            order_dict["items"].append({
                "order_item_id": item.id,
                "product_variant_id": item.product_variant_id,
                "product_name": (
                item.product_variant.product.name
                if item.product_variant and item.product_variant.product
                else None
            ),

                "quantity": item.quantity,
                "shipped_quantity": item.shipped_quantity,
                "price": item.price
            })

        # Include shipments and warehouse info
        for shipment in order.shipments:
            shipment_dict = {
                "shipment_id": shipment.id,
                "warehouse_id": shipment.warehouse_id,
                "warehouse_name": shipment.warehouse.name if shipment.warehouse else None,
                "carrier": shipment.carrier,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "items": [
                    {
                        "order_item_id": si.order_item_id,
                        "quantity": si.quantity
                    }
                    for si in shipment.items
                ]
            }
            order_dict["shipments"].append(shipment_dict)

        result.append(order_dict)

    return result



