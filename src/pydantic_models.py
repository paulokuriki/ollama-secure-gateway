from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    is_active: bool = None

class UserInDB(User):
    disabled: bool = None
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class NewUserRequest(BaseModel):
    username: str
    full_name: str
    email: EmailStr
    password: str