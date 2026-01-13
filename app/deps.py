from fastapi import Depends, HTTPException
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# decode token to get user
def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

# role check dependencies
def admin_only(user=Depends(get_current_user)):
    if user.get("role") != "ADMIN":
        raise HTTPException(403, "Admin access required")
    return user

def cashier_only(user=Depends(get_current_user)):
    if user.get("role") != "CASHIER":
        raise HTTPException(403, "Cashier access required")
    return user

def admin_or_cashier(user=Depends(get_current_user)):
    if user.get("role") not in ["ADMIN", "CASHIER"]:
        raise HTTPException(403, "Admin or Cashier access required")
    return user
