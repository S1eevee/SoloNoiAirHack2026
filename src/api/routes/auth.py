"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from src.auth.auth import (
    register_user, authenticate_user, create_access_token, verify_token,
    get_user_by_id, save_fcm_token, Token, User
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Schemas
class RegisterRequest(BaseModel):
    employee_id: str
    name: str
    email: EmailStr
    password: str
    role: str = "employee"  # "supervisor" or "employee"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FCMTokenRequest(BaseModel):
    fcm_token: str

class UserResponse(BaseModel):
    employee_id: str
    name: str
    email: str
    role: str

# Dependency: get current user
async def get_current_user(token: str = None) -> User:
    """Extract and validate JWT token from request."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    employee_id = verify_token(token)
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = get_user_by_id(employee_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Endpoints
@router.post("/register", response_model=dict)
async def register(req: RegisterRequest):
    """Register a new employee account."""
    if register_user(req.employee_id, req.name, req.email, req.password, req.role):
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=400, detail="Email or employee ID already exists")

@router.post("/login", response_model=Token)
async def login(req: LoginRequest):
    """Login with email and password. Returns JWT token."""
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(user.employee_id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        employee_id=user.employee_id,
        name=user.name
    )

@router.post("/fcm-token")
async def save_fcm_token_endpoint(req: FCMTokenRequest, token: str):
    """Save Firebase Cloud Messaging token for push notifications."""
    employee_id = verify_token(token)
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if save_fcm_token(employee_id, req.fcm_token):
        return {"message": "FCM token saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save FCM token")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token: str):
    """Get current user info."""
    employee_id = verify_token(token)
    if employee_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = get_user_by_id(employee_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse(
        employee_id=user.employee_id,
        name=user.name,
        email=user.email,
        role=user.role
    )
