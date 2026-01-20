from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin

from ..database import SessionLocal
from ..models import User
from ..auth import hash_password, create_token

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

    db_user = User(
        email=user.email,
        password=hash_password(user.password),
        role=user.role
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
    if not db_user:
        raise HTTPException(401, "Invalid credentials")

    # Include role in token
    token_data = {"sub": db_user.email, "role": db_user.role}
    token = create_token(token_data)

    return {"access_token": token}

