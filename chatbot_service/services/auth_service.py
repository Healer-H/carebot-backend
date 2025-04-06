# services/auth_service.py
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from config import settings
from models.user import User

class AuthService:
    @staticmethod
    def create_access_token(user: User) -> str:
        """
        Create a JWT access token for the user
        """
        # Define token data
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "exp": datetime.utcnow() + settings.TOKEN_EXPIRE_TIME
        }
        
        # Create token
        token = jwt.encode(
            payload,
            settings.TOKEN_SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """
        Decode and validate JWT token
        """
        try:
            payload = jwt.decode(
                token,
                settings.TOKEN_SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Validate expiration
            if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
                return None
                
            return payload
        except jwt.PyJWTError:
            return None