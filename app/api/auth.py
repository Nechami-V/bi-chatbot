"""
Authentication API endpoints
Login, user info, and permission checking
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import base64
import json
import hmac
import hashlib

try:
    import jwt  # PyJWT
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from app.services.user_service import get_user_db_manager
from app.services.permission_service import PermissionManager
from app.models.user import User
from app.simple_config import config as app_config

# Security
security = HTTPBearer()
ALGORITHM = "HS256"

# Load from environment/config
SECRET_KEY = app_config.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = app_config.ACCESS_TOKEN_EXPIRE_MINUTES

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
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _create_signed_simple_token(payload: dict) -> str:
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"simple.{payload_b64}.{sig_b64}"


def _verify_signed_simple_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != "simple":
            return None
        _, payload_b64, sig_b64 = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected_sig), sig_b64):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode())
        return payload
    except Exception:
        return None


def create_access_token(user_id: int, email: str) -> str:
    """Create access token (JWT if available, otherwise signed simple token)."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "email": email, "exp": int(expire.timestamp())}

    if JWT_AVAILABLE:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Signed simple fallback
    return _create_signed_simple_token(payload)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify token and return user"""
    token = credentials.credentials
    
    try:
        payload = None
        user_id = None
        email = None

        # Prefer JWT
        if JWT_AVAILABLE and not token.startswith("simple_"):
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        else:
            # Support legacy simple_ tokens
            if token.startswith("simple_"):
                legacy_token = token[7:]
                try:
                    token_json = base64.b64decode(legacy_token.encode()).decode()
                    payload = json.loads(token_json)
                except Exception:
                    payload = None
            # Signed simple tokens: simple.<payload>.<sig>
            if payload is None:
                payload = _verify_signed_simple_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Expiration check
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > float(exp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("user_id")
        email = payload.get("email")

        if user_id is None and not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_db_manager = get_user_db_manager()
    user = None
    if user_id is not None:
        user = user_db_manager.get_user_by_id(user_id)
    if user is None and email:
        user = user_db_manager.get_user_by_email(email)
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
    
    # Authenticate user against SQL Server
    user_db_manager = get_user_db_manager()
    user = user_db_manager.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(user.id, user.email)
    
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
    
    user_db_manager = get_user_db_manager()
    users = user_db_manager.get_all_users()
    return {
        "users": [user.to_dict() for user in users],
        "total": len(users)
    }
