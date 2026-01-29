from fastapi import Depends, HTTPException, Header
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# -------------------------
# Decode token from Authorization header
# -------------------------
def get_current_user(authorization: str = Header(...)):
    """
    Reads the token from the Authorization header in the format:
    Authorization: Bearer <token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    token = authorization.split(" ")[1]  # extract token after "Bearer"
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("JWT payload:", payload)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# -------------------------
# Role-based dependencies
# -------------------------
def admin_only(user=Depends(get_current_user)):
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def cashier_only(user=Depends(get_current_user)):
    if user.get("role") != "CASHIER":
        raise HTTPException(status_code=403, detail="Cashier access required")
    return user

def admin_or_cashier(user=Depends(get_current_user)):
    if user.get("role") not in ["ADMIN", "CASHIER"]:
        raise HTTPException(status_code=403, detail="Admin or Cashier access required")
    return user
