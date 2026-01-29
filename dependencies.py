from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-that-should-be-kept-secret")
ALGORITHM = "HS256"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates session token and returns current user information
    """
    try:
        token = credentials.credentials

        # Check if it's a simple session token (legacy email.session format)
        if token.endswith(".session"):
            email = token.replace(".session", "")
            return {"email": email, "role": "user", "is_admin": False}

        # Otherwise try JWT validation with role support
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no email found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = payload.get("role", "user")
        return {"email": email, "role": role, "is_admin": role == "admin"}
    except JWTError:
        # If JWT fails, try session token format
        try:
            token = credentials.credentials
            if token.endswith(".session"):
                email = token.replace(".session", "")
                return {"email": email, "role": "user", "is_admin": False}
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin(user: dict = Depends(get_current_user)):
    """
    Ensures the caller is an admin user using JWT role claims.
    """
    email = user.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user email in token",
        )

    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return {"email": email, "is_admin": True}