"""
Authentication API endpoints
Login, user info, and permission checking
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Simple fallback token system
    import base64
    import json
from app.services.user_service import user_db
from app.services.permission_service import PermissionManager
from app.models.user import User
from app.simple_config import config

# Security
security = HTTPBearer()
SECRET_KEY = config.SECRET_KEY  # Loaded from .env via simple_config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict
    permissions: dict

class UserInfoResponse(BaseModel):
    user: dict
    permissions: dict

# Helper functions
def create_access_token(user_id: int) -> str:
    """Create access token (JWT or simple)"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    if JWT_AVAILABLE:
        to_encode = {"user_id": user_id, "exp": expire}
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    else:
        # Simple token fallback
        token_data = {
            "user_id": user_id, 
            "exp": expire.timestamp()
        }
        token_json = json.dumps(token_data)
        token_b64 = base64.b64encode(token_json.encode()).decode()
        return f"simple_{token_b64}"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify token and return user"""
    token = credentials.credentials
    
    try:
        if JWT_AVAILABLE and not token.startswith("simple_"):
            # JWT token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
        else:
            # Simple token
            if token.startswith("simple_"):
                token = token[7:]  # Remove "simple_" prefix
            
            token_json = base64.b64decode(token.encode()).decode()
            token_data = json.loads(token_json)
            
            # Check expiration
            if datetime.utcnow().timestamp() > token_data["exp"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_id = token_data.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_db.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# API Endpoints
@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """User login endpoint"""
    
    # Authenticate user
    user = user_db.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(user.id)
    
    # Get permissions
    permissions = PermissionManager.get_permission_info(user)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_info=user.to_dict(),
        permissions=permissions
    )

@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(current_user: User = Depends(verify_token)):
    """Get current user information"""
    
    permissions = PermissionManager.get_permission_info(current_user)
    
    return UserInfoResponse(
        user=current_user.to_dict(),
        permissions=permissions
    )

@router.get("/check-access/{table_name}")
async def check_table_access(table_name: str, current_user: User = Depends(verify_token)):
    """Check if current user has access to specific table"""
    
    has_access = PermissionManager.check_table_access(current_user, table_name)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to table '{table_name}' for permission group '{current_user.permission_group}'"
        )
    
    return {
        "table": table_name,
        "access_granted": True,
        "user": current_user.full_name,
        "permission_group": current_user.permission_group
    }

@router.get("/users")
async def list_users(current_user: User = Depends(verify_token)):
    """List all users (admin only)"""
    
    if not PermissionManager.can_access_all_data(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = user_db.get_all_users()
    return {
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }
