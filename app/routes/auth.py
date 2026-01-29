from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin

from ..database import SessionLocal
from ..models import User
from ..auth import hash_password, create_token, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Optional: validate role
    
    if user.role not in ["ADMIN", "CASHIER", "USER"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user.email,
        password=hash_password(user.password),
        role=user.role,
        full_name=user.full_name,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "message": "User registered",
        "user_id": db_user.id,
        "role": db_user.role
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ sub MUST be the user ID
    token = create_token({
        "sub": str(db_user.id),
        "role": db_user.role,
        "email": db_user.email
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role
    }


