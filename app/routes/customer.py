from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Address, Order
from app.schemas.customer import SegmentUpdate, UserOut, AddressCreate, AddressOut
from app.deps import admin_only, get_current_user

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

# list customers

@router.get("/", response_model=list[UserOut], dependencies=[Depends(admin_only)])
def list_customers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(User)
    return query.offset(skip).limit(limit).all()

# customer profile and ownership
@router.get("/get-profile", response_model=UserOut)
def get_my_profile(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).get(user["sub"])
    return db_user

# list customer by id

@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(admin_only)])
def get_customer_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# change customer segment
@router.patch("/{user_id}/segment", dependencies=[Depends(admin_only)])
def update_customer_segment(
    user_id: int,
    payload: SegmentUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(User).get(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.segment not in ["REGULAR", "VIP", "WHOLESALE"]:
        raise HTTPException(status_code=400, detail="Invalid segment")

    user.customer_segment = payload.segment
    db.commit()

    return {
        "message": "Customer segment updated",
        "user_id": user_id,
        "customer_segment": user.customer_segment
    }

# order history
@router.get("/me/orders")
def my_orders(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Order).filter(Order.user_id == user["sub"]).all()


# address book management
@router.post("/me/addresses", response_model=AddressOut)
def add_my_address(
    address: AddressCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_address = Address(user_id=user["sub"], **address.dict())
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


@router.get("/me/addresses", response_model=list[AddressOut])
def get_my_addresses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Address).filter(Address.user_id == user["sub"]).all()

# delete adresses
@router.delete("/me/addresses/{address_id}")
def delete_my_address(
    address_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    address = (
        db.query(Address)
        .filter(
            Address.id == address_id,
            Address.user_id == int(user["sub"])
        )
        .first()
    )

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(address)
    db.commit()

    return {"message": "Address deleted"}


# guest checkout
@router.post("/guest", response_model=UserOut)
def create_guest(db: Session = Depends(get_db)):
    guest = User(
        role="GUEST",
        is_active=True
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


# GDPR / Delete Customer
@router.delete("/me")
def gdpr_self_delete(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).get(user["sub"])

    db_user.email = None
    db_user.phone = None
    db_user.password = None
    db_user.is_active = False
    db_user.deleted_at = datetime.utcnow()

    db.commit()
    return {"message": "Account anonymized per GDPR"}

