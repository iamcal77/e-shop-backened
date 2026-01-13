from passlib.context import CryptContext
from jose import jwt
import os
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# Password hashing context using Argon2 (no 72-byte limit)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# ----------------------------
# Password Hashing / Verification
# ----------------------------
def hash_password(password: str) -> str:
    """
    Hash a password using Argon2.
    """
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash using Argon2.
    """
    return pwd_context.verify(password, hashed)

# ----------------------------
# JWT Token Creation
# ----------------------------
def create_token(data: dict) -> str:
    """
    Create a JWT token with expiration.
    """
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
 