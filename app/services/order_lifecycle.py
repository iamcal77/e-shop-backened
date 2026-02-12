from app.constants.order_status import OrderStatus

ALLOWED_TRANSITIONS = {
    OrderStatus.CREATED: [
        OrderStatus.PAID,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.PAID: [
        OrderStatus.PROCESSING,
        OrderStatus.CANCELLED,
    ],
    OrderStatus.PROCESSING: [
        OrderStatus.PARTIALLY_SHIPPED,
        OrderStatus.SHIPPED,
    ],
    OrderStatus.PARTIALLY_SHIPPED: [
        OrderStatus.SHIPPED,
    ],
    OrderStatus.SHIPPED: [
        OrderStatus.COMPLETED,
    ],
    OrderStatus.CANCELLED: [
        OrderStatus.REFUNDED,
    ],
}


def can_transition(current_status: str, new_status: str) -> bool:
    return new_status in ALLOWED_TRANSITIONS.get(current_status, [])
