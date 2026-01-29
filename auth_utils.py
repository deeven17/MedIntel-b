# Assuming this code is in a file named auth_utils.py

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# This is a dummy secret key. In a real app, use a strong, random key from an environment variable.
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-that-should-be-kept-secret")
ALGORITHM = "HS256"

# This object handles the authentication flow for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a new JWT token with session management.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)  # 30 minutes for better UX
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    Creates a refresh token that lasts longer for session persistence.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days for refresh token
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str):
    """
    Verifies a refresh token and returns the payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        exp: int = payload.get("exp")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
        # Check if token is expired
        current_time = datetime.now(timezone.utc).timestamp()
        if current_time > exp:
            raise credentials_exception
            
        return {"id": user_id}
    except JWTError:
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the JWT token and returns the user payload with session validation.
    Enhanced for better session management and security.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        exp: int = payload.get("exp")
        iat: int = payload.get("iat")
        
        if user_id is None or exp is None:
            raise credentials_exception
            
        # Check if token is expired
        current_time = datetime.now(timezone.utc).timestamp()
        if current_time > exp:
            raise credentials_exception
            
        # Check if token was issued in the future (clock skew protection)
        if iat > current_time:
            raise credentials_exception
            
        # In a real application, you would fetch the user from a database here
        # and validate the session against stored sessions
        return {
            "id": user_id,
            "exp": exp,
            "iat": iat
        }
    except JWTError:
        raise credentials_exception