import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_jwt_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock User DB (In-memory for demo)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

MOCK_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": hash_password("admin123"), # password: admin123
        "role": "Admin",
        "tenant": "all" # Admins can see all tenants
    },
    "viewerA": {
        "username": "viewerA",
        "password_hash": hash_password("viewer123"), # password: viewer123
        "role": "Viewer",
        "tenant": "demoA"
    },
    "viewerB": {
        "username": "viewerB",
        "password_hash": hash_password("viewer123"), # password: viewer123
        "role": "Viewer",
        "tenant": "demoB"
    },
    # Fluent Bit / API Ingestion Account
    "fluentbit": {
        "username": "fluentbit",
        # For assignment simplicity, the password for the service account is the INGEST_TOKEN
        "password_hash": hash_password(os.getenv("INGEST_TOKEN", "demo_secret_token")),
        "role": "Service",
        "tenant": "all"
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    role: str
    tenant: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user(username: str):
    if username in MOCK_USERS:
        return MOCK_USERS[username]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Check if the token is the static INGEST_TOKEN for fluent-bit backwards compatibility
        # If the token exactly matches our INGEST_TOKEN, authenticate as fluentbit
        # This is a fallback so Fluent Bit configuration doesn't break.
        if token == os.getenv("INGEST_TOKEN", "demo_secret_token"):
            return User(username="fluentbit", role="Service", tenant="all")
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user["username"], role=user["role"], tenant=user["tenant"])
