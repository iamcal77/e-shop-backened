from sqlalchemy import Boolean, Column, DateTime, Integer, String, Float, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .database import Base

# -------------------------
# Users
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    sso_provider = Column(String, nullable=True)
    sso_id = Column(String, nullable=True)
    role = Column(String, default="USER")  # ADMIN, CASHIER, CUSTOMER
    is_active = Column(Boolean, default=True)
    loyalty_points = Column(Integer, default=0)
    customer_segment = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    addresses = relationship("Address", back_populates="user")
    carts = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

# -------------------------
# Addresses
# -------------------------
class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    line1 = Column(String)
    city = Column(String)
    country = Column(String)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")

# -------------------------
# Categories
# -------------------------
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], backref="subcategories")

# -------------------------
# Products & Variants
# -------------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(Text)
    product_type = Column(String)  # physical | digital | service
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    variants = relationship("ProductVariant", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))

    sku = Column(String, unique=True)
    price = Column(Float)

    size = Column(String, nullable=True)
    color = Column(String, nullable=True)

    weight_kg = Column(Float, default=0)
    is_active = Column(Boolean, default=True)

    product = relationship("Product", back_populates="variants")

class ShippingRate(Base):
    __tablename__ = "shipping_rates"

    id = Column(Integer, primary_key=True)
    country = Column(String, nullable=False)

    min_weight = Column(Float, default=0)
    max_weight = Column(Float, nullable=True)

    price = Column(Float, nullable=False)


# -------------------------
# Warehouses & Inventory
# -------------------------
class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)

    inventory = relationship("Inventory", back_populates="warehouse")
    shipments = relationship("Shipment", back_populates="warehouse")

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=5)

    product_variant = relationship("ProductVariant", back_populates="inventory")
    warehouse = relationship("Warehouse", back_populates="inventory")

# -------------------------
# Cart & Cart Items
# -------------------------
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True)

    # Nullable → supports guest checkout
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_email = Column(String, nullable=True)

    is_abandoned = Column(Boolean, default=False)
    last_activity_at = Column(DateTime, server_default=func.now())

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="carts")
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan"
    )

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)

    cart_id = Column(
        Integer,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False
    )

    # IMPORTANT: variant, not product
    product_variant_id = Column(
        Integer,
        ForeignKey("product_variants.id"),
        nullable=False
    )

    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    product_variant = relationship("ProductVariant")

# -------------------------
# Orders & Order Items
# -------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    guest_email = Column(String, nullable=True)

    source = Column(String)  # POS | ONLINE
    status = Column(String, default="CREATED")

    total = Column(Float, default=0)
    shipping_cost = Column(Float, default=0)
    currency = Column(String, default="KES")

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    payment = relationship("Payment", back_populates="order", uselist=False)
    shipment = relationship("Shipment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float)

    order = relationship("Order", back_populates="items")
    product_variant = relationship("ProductVariant", back_populates="order_items")

class OrderAddress(Base):
    __tablename__ = "order_addresses"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))

    line1 = Column(String)
    city = Column(String)
    country = Column(String)

    order = relationship("Order", backref="shipping_address")

# -------------------------
# Payments
# -------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    provider = Column(String)  # MPESA, STRIPE
    reference = Column(String)
    status = Column(String)  # PENDING, SUCCESS, FAILED
    amount = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="payments")

# -------------------------
# Shipments
# -------------------------
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    carrier = Column(String)
    tracking_number = Column(String)
    status = Column(String)

    order = relationship("Order", back_populates="shipments")
    warehouse = relationship("Warehouse", back_populates="shipments")



# -------------------------
# Discount & Coupon
# -------------------------
class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True)
    type = Column(String)  # percentage | fixed | tiered
    value = Column(Float)  # For tiered, max discount
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    customer_segment = Column(String, nullable=True)  # optional, e.g., VIP, Wholesale

    coupons = relationship("Coupon", back_populates="discount")

class Coupon(Base):
    __tablename__ = "coupons"

    code = Column(String, primary_key=True)
    discount_id = Column(Integer, ForeignKey("discounts.id"))
    usage_limit = Column(Integer, default=1)

    discount = relationship("Discount", back_populates="coupons")

# -------------------------
# Dynamic Pricing / Price Rules
# -------------------------
class PriceRule(Base):
    __tablename__ = "price_rules"

    id = Column(Integer, primary_key=True)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"))
    customer_segment = Column(String, nullable=True)
    region = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    product_variant = relationship("ProductVariant", backref="price_rules")

# -------------------------
# Tax Rules
# -------------------------
class TaxRule(Base):
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True)
    region = Column(String, nullable=False)
    tax_percentage = Column(Float, nullable=False)
    active = Column(Boolean, default=True)

