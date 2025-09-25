import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import config
from .db.database import get_db
from .models.user import User, APIKey

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY_NAME = "X-API-Key"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Password hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# API Key management
async def get_api_key(api_key: str = Depends(api_key_header), db: Session = Depends(get_db)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is missing"
        )
    
    db_key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    # Update last used timestamp
    db_key.last_used_at = datetime.utcnow()
    db.commit()
    
    return db_key

def create_api_key(user_id: int, db: Session, description: str = None) -> str:
    """Generate a new API key for a user"""
    key = f"sk_{secrets.token_urlsafe(32)}"
    db_key = APIKey(
        key=key,
        user_id=user_id,
        description=description,
        created_at=datetime.utcnow(),
        last_used_at=None,
        is_active=True
    )
    db.add(db_key)
    db.commit()
    return key

# Rate limiting
class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 900):  # 100 requests per 15 minutes by default
        self.requests = requests
        self.window = window
        self.tokens = {}
    
    async def __call__(self, request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Get or initialize token bucket for this IP
        now = datetime.utcnow().timestamp()
        if client_ip not in self.tokens:
            self.tokens[client_ip] = {
                'tokens': self.requests,
                'last_update': now
            }
        
        # Calculate new token count
        bucket = self.tokens[client_ip]
        time_passed = now - bucket['last_update']
        bucket['tokens'] += time_passed * (self.requests / self.window)
        bucket['tokens'] = min(bucket['tokens'], self.requests)
        bucket['last_update'] = now
        
        # Check if request is allowed
        if bucket['tokens'] < 1:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests"
            )
        
        # Deduct a token
        bucket['tokens'] -= 1
        
        # Process the request
        response = await call_next(request)
        return response

# Initialize rate limiter
rate_limiter = RateLimiter()
