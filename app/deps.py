from fastapi import Depends, HTTPException, Header
from jose import jwt
import os
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# -------------------------
# Decode token from Authorization header
# -------------------------
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """
    Returns the full User ORM object from the JWT token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Fetch user from database
        user = db.query(User).get(int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -------------------------
# Role-based dependencies
# -------------------------
def admin_only(user=Depends(get_current_user)):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def cashier_only(user=Depends(get_current_user)):
    if user.role != "CASHIER":
        raise HTTPException(status_code=403, detail="Cashier access required")
    return user

def admin_or_cashier(user=Depends(get_current_user)):
    if user.role not in ["ADMIN", "CASHIER"]:
        raise HTTPException(status_code=403, detail="Admin or Cashier access required")
    return user
