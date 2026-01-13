from sqlalchemy import Boolean, Column, DateTime, Integer, String, Float, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="USER")  # ADMIN / USER

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)
    sku = Column(String, unique=True, nullable=True)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    total = Column(Float)
    status = Column(String, default="PENDING")

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True)
    quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=5)

    product = relationship("Product")
    
class POSOrder(Base):
    __tablename__ = "pos_orders"

    id = Column(Integer, primary_key=True)
    cashier_id = Column(Integer, ForeignKey("users.id"))
    total = Column(Float)
    payment_method = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class POSOrderItem(Base):
    __tablename__ = "pos_order_items"

    id = Column(Integer, primary_key=True)
    pos_order_id = Column(Integer, ForeignKey("pos_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price = Column(Float)
    product = relationship("Product")
