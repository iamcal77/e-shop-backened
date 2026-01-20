from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Address, Order
from app.schemas.customer import UserCreate, UserOut, AddressCreate, AddressOut
from app.deps import admin_only

router = APIRouter(prefix="/customers", tags=["Customer Management"])

# -------------------------
# DB Dependency
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Customer Registration
# -------------------------
@router.post("/", response_model=UserOut)
def register_customer(user: UserCreate, db: Session = Depends(get_db)):
    if not user.email and not user.phone and not user.sso_id:
        raise HTTPException(400, "Provide at least email, phone, or SSO ID")
    
    existing_user = None
    if user.email:
        existing_user = db.query(User).filter(User.email == user.email).first()
    if user.phone and not existing_user:
        existing_user = db.query(User).filter(User.phone == user.phone).first()
    if existing_user:
        raise HTTPException(400, "User already exists")
    
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# -------------------------
# Guest Checkout / Create Guest
# -------------------------
@router.post("/guest", response_model=UserOut)
def create_guest(db: Session = Depends(get_db)):
    guest = User(role="GUEST", is_active=True)
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest

# -------------------------
# List Customers / Profiles
# -------------------------
@router.get("/", response_model=list[UserOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(User).all()

# -------------------------
# Customer Address Management
# -------------------------
@router.post("/{user_id}/addresses", response_model=AddressOut)
def add_address(user_id: int, address: AddressCreate, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    new_address = Address(user_id=user.id, **address.dict())
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.get("/{user_id}/addresses", response_model=list[AddressOut])
def get_addresses(user_id: int, db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == user_id).all()

# -------------------------
# GDPR / Delete Customer
# -------------------------
@router.delete("/{user_id}")
def delete_customer(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    # Optional: anonymize personal data before deleting orders/cart for GDPR
    user.email = None
    user.phone = None
    user.password = None
    user.is_active = False
    db.commit()
    return {"message": f"User {user_id} deactivated / anonymized for GDPR"}
