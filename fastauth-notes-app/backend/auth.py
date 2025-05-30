import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, PasswordReset

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    hashed_password: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user = Depends(get_current_user)):
    return current_user


def create_password_reset_token(email: str, db: Session):
    # Generate a secure token
    token = secrets.token_urlsafe(32)
    
    # Set expiration time (24 hours from now)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Get user by email
    user = get_user_by_email(db, email)
    if not user:
        # We don't want to reveal if the email exists or not for security reasons
        return None
    
    # Check if there's an existing reset token for this user
    existing_reset = db.query(PasswordReset).filter(PasswordReset.user_id == user.id).first()
    
    if existing_reset:
        # Update existing reset token
        existing_reset.token = token
        existing_reset.expires_at = expires_at
    else:
        # Create new reset token
        reset_entry = PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.add(reset_entry)
    
    db.commit()
    return token


def verify_password_reset_token(token: str, db: Session):
    # Find the reset entry
    reset_entry = db.query(PasswordReset).filter(PasswordReset.token == token).first()
    
    if not reset_entry:
        return None
    
    # Check if token is expired
    if reset_entry.expires_at < datetime.utcnow():
        # Delete expired token
        db.delete(reset_entry)
        db.commit()
        return None
    
    # Get the user
    user = db.query(User).filter(User.id == reset_entry.user_id).first()
    return user


def reset_password(token: str, new_password: str, db: Session):
    # Verify token and get user
    user = verify_password_reset_token(token, db)
    
    if not user:
        return False
    
    # Update user's password
    user.hashed_password = get_password_hash(new_password)
    
    # Delete the reset token
    reset_entry = db.query(PasswordReset).filter(PasswordReset.user_id == user.id).first()
    db.delete(reset_entry)
    
    db.commit()
    return True