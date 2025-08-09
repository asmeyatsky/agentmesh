from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

SECRET_KEY = "your-secret-key"  # In a real app, this should be loaded from environment variables or a secure vault
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload is None:
            raise credentials_exception
        return payload
    except JWTError as e:
        logger.error(f"JWT Error: {e}")
        raise credentials_exception
