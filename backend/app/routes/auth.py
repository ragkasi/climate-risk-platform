"""
Authentication routes for OTP-based login.
"""

import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.config import settings
from app.db.models import User
from app.db.database import get_db
from app.utils.sanitize import sanitize_text

router = APIRouter()
security = HTTPBearer()

# Redis client for OTP storage
redis_client = redis.from_url(settings.redis_url)


class OTPRequest(BaseModel):
    """OTP request model."""
    email: EmailStr


class OTPVerify(BaseModel):
    """OTP verification model."""
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


async def send_otp_email(email: str, code: str) -> bool:
    """
    Send OTP code via email.
    
    Args:
        email: Recipient email
        code: OTP code
        
    Returns:
        True if sent successfully
    """
    if not settings.smtp_host or not settings.smtp_user:
        # In demo mode, just log the OTP
        print(f"DEMO MODE: OTP for {email} is {code}")
        return True
    
    try:
        msg = MIMEText(f"Your Climate Risk Lens verification code is: {code}")
        msg["Subject"] = "Climate Risk Lens - Verification Code"
        msg["From"] = settings.smtp_from
        msg["To"] = email
        
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@router.post("/request_otp", response_model=dict)
async def request_otp(otp_request: OTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Request OTP code for email verification.
    
    Args:
        otp_request: Email address
        db: Database session
        
    Returns:
        Success message
    """
    email = sanitize_text(otp_request.email)
    
    # Generate 6-digit OTP
    otp_code = str(secrets.randbelow(900000) + 100000)
    
    # Store OTP in Redis with 5-minute expiry
    otp_key = f"otp:{email}"
    await redis_client.setex(otp_key, 300, otp_code)  # 5 minutes
    
    # Send OTP via email
    email_sent = await send_otp_email(email, otp_code)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code"
        )
    
    return {
        "message": "Verification code sent to your email",
        "email": email,
        "expires_in": 300
    }


@router.post("/verify_otp", response_model=TokenResponse)
async def verify_otp(otp_verify: OTPVerify, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP code and return JWT token.
    
    Args:
        otp_verify: Email and OTP code
        db: Database session
        
    Returns:
        JWT access token
    """
    email = sanitize_text(otp_verify.email)
    code = sanitize_text(otp_verify.code)
    
    # Verify OTP from Redis
    otp_key = f"otp:{email}"
    stored_code = await redis_client.get(otp_key)
    
    if not stored_code or stored_code.decode() != code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code"
        )
    
    # Remove OTP after successful verification
    await redis_client.delete(otp_key)
    
    # Get or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            is_verified=True,
            role="anon"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        await db.commit()
    
    # Generate JWT token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
