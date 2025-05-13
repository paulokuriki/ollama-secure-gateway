from fastapi import FastAPI, Depends, HTTPException, Request, status, Body
from pydantic_models import *
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import jwt
import constants as c
import database as db
import bcrypt

# OAuth2 Bearer token setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Check if the provided password matches the stored password (hashed)
def verify_password(plain_password, hashed_password):
    # Encode the plain password to bytes
    password_byte_enc = plain_password.encode('utf-8')

    # If the hashed_password is a string, decode it to bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    # Verify the password
    return bcrypt.checkpw(password=password_byte_enc, hashed_password=hashed_password)


def get_user(db, username: str):
    for user in db:
        if user["username"] == username:
            return UserInDB(**user)
    return None

def authenticate_user(username: str, password: str):
    tb_users = db.load_db()
    user = get_user(tb_users, username)
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, c.SECRET_KEY, algorithm=c.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, c.SECRET_KEY, algorithms=[c.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    tb_users = db.load_db()
    user = get_user(tb_users, username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

