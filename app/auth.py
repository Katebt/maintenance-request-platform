from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models

import os

# ✅ تحميل المتغيرات من .env في بيئة التطوير فقط
if os.getenv("ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

# ✅ إعداد المتغيرات
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

if not SECRET_KEY:
    raise RuntimeError("❌ SECRET_KEY is missing from environment variables!")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------- Password hashing ----------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ---------- Token handling ----------
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Auth dependencies ----------
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    user = db.query(models.User).filter(models.User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_optional_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            return None
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except Exception:
        return None

# ---------- Password Reset ----------
def create_reset_token(email: str, expires_minutes: int = 30):
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None