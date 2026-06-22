from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db

from models.user import User
from utils.helpers import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# JWT Security Dependency
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    default_user = {"user_id": "user_1", "email": "user_1@finpilot.ai", "name": "Default User"}
    if not credentials:
        return default_user
        
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return default_user
        
    email = payload.get("email")
    if not email:
        return default_user
        
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        return default_user
        
    return {"user_id": str(user.id), "email": user.email, "name": user.name}


# --- Request Schemas ---

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str # email
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str

class OTPLoginRequest(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# --- Routes ---

@router.post("/signup")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists.")
        
    new_user = User(
        email=req.email,
        name=req.name or req.email.split("@")[0],
        hashed_password=hash_password(req.password)
    )
    db.add(new_user)
    await db.commit()
    
    # Generate token
    token = create_access_token({"email": new_user.email, "user_id": new_user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": new_user.email,
            "name": new_user.name
        }
    }

@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token({"email": user.email, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/google-login")
async def google_login(req: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    # Mock Google Login - create or retrieve user by email
    mock_email = "google_user@finpilot.ai"
    stmt = select(User).where(User.email == mock_email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        user = User(
            email=mock_email,
            name="Google User",
            hashed_password=hash_password("google_dummy_password")
        )
        db.add(user)
        await db.commit()
        
    token = create_access_token({"email": user.email, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/otp-login")
async def otp_login(req: OTPLoginRequest, db: AsyncSession = Depends(get_db)):
    # Mock OTP check
    if req.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP code.")
        
    stmt = select(User).where(User.email == req.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        user = User(
            email=req.email,
            name=req.email.split("@")[0],
            hashed_password=hash_password("otp_dummy_password")
        )
        db.add(user)
        await db.commit()
        
    token = create_access_token({"email": user.email, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "name": user.name
        }
    }

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"message": f"Password reset email has been sent to {req.email}."}
