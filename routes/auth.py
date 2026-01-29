import os
from fastapi import APIRouter, HTTPException
from database import users_col
import bcrypt
from datetime import datetime, timedelta

from auth_utils import create_access_token

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

@router.post("/register")
async def register(data: dict):
    email = data.get("email")
    password = data.get("password")
    is_admin = bool(data.get("is_admin"))

    if not email or not password:
        raise HTTPException(400, "Email and password required")

    if await users_col.find_one({"email": email}):
        raise HTTPException(400, "User already exists")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    await users_col.insert_one(
        {
            "email": email,
            "password": hashed,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "is_active": False,
            "is_admin": is_admin,
        }
    )
    return {"ok": True}

@router.post("/login")
async def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    user = await users_col.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")

    stored = user.get("password")
    if not stored:
        raise HTTPException(500, "Corrupted user record")

    if not bcrypt.checkpw(password.encode(), stored.encode()):
        raise HTTPException(401, "Invalid credentials")

    # Update last_login and mark user as active
    await users_col.update_one(
        {"email": email},
        {
            "$set": {
                "last_login": datetime.utcnow(),
                "is_active": True,
            }
        },
    )

    # Issue a JWT access token; expiry from env (default 60 min) for safety
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email, "role": "admin" if user.get("is_admin") else "user"},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "email": email,
            "is_admin": user.get("is_admin", False),
        },
    }
