import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from .database import get_database

# Secret key and algorithm for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserInDB(BaseModel):
    email: str
    username: str
    hashed_password: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user_by_email(db, email: str):
    return await db.users.find_one({"email": email})


async def authenticate_user(db, username: str, password: str):
    user = await db.users.find_one({"username": username})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
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


async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    if current_user.get("disabled", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def create_user(db, user_data):
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user document
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "disabled": False,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = await db.users.insert_one(user_doc)
    
    return result.inserted_id


async def create_password_reset_token(email: str, db):
    # Generate a secure token
    token = secrets.token_urlsafe(32)
    
    # Set expiration time (24 hours from now)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Get user by email
    user = await db.users.find_one({"email": email})
    if not user:
        # We don't want to reveal if the email exists or not for security reasons
        return None
    
    # Check if there's an existing reset token for this user
    existing_reset = await db.password_resets.find_one({"user_id": user["_id"]})
    
    if existing_reset:
        # Update existing reset token
        await db.password_resets.update_one(
            {"_id": existing_reset["_id"]},
            {"$set": {"token": token, "expires_at": expires_at}}
        )
    else:
        # Create new reset token
        await db.password_resets.insert_one({
            "user_id": user["_id"],
            "token": token,
            "expires_at": expires_at
        })
    
    return token


async def verify_password_reset_token(token: str, db):
    # Find the reset entry
    reset_entry = await db.password_resets.find_one({"token": token})
    
    if not reset_entry:
        return None
    
    # Check if token is expired
    if reset_entry["expires_at"] < datetime.utcnow():
        # Delete expired token
        await db.password_resets.delete_one({"_id": reset_entry["_id"]})
        return None
    
    # Get the user
    user = await db.users.find_one({"_id": reset_entry["user_id"]})
    return user


async def reset_password(token: str, new_password: str, db):
    # Verify token and get user
    user = await verify_password_reset_token(token, db)
    
    if not user:
        return False
    
    # Update user's password
    hashed_password = get_password_hash(new_password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hashed_password}}
    )
    
    # Delete the reset token
    await db.password_resets.delete_one({"user_id": user["_id"]})
    
    return True