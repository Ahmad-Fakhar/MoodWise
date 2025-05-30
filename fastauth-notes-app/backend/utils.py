import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr
from bson import ObjectId

from .models import TokenData, UserInDB
from .database import db

# Load environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_jwt_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Email validation regex
email_regex = re.compile(r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing
    """
    return pwd_context.hash(password)


async def get_user(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by email from the database
    """
    user = await db.users.find_one({"email": email})
    return user


async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user by email and password
    """
    user = await get_user(email)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user from a JWT token
    """
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
    user = await get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get the current active user
    """
    if current_user.get("disabled", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def validate_email(email: str) -> bool:
    """
    Validate an email address format
    """
    return bool(email_regex.match(email))


def generate_reset_token() -> str:
    """
    Generate a secure token for password reset
    """
    return secrets.token_urlsafe(32)


def format_object_id(obj_id: ObjectId) -> str:
    """
    Format an ObjectId to string
    """
    return str(obj_id)


def parse_object_id(id_str: str) -> ObjectId:
    """
    Parse a string to ObjectId
    """
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )


def extract_emotion_from_text(text: str) -> str:
    """
    Extract emotion tag from text
    Format: [EMOTION: emotion_name]
    """
    emotion_match = re.search(r'\[EMOTION:\s*(\w+)\]', text)
    if emotion_match:
        emotion = emotion_match.group(1).lower()
        # Clean text by removing the tag
        clean_text = re.sub(r'\[EMOTION:\s*\w+\]', '', text).strip()
        return emotion, clean_text
    return "neutral", text