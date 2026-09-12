from pydantic import BaseModel,EmailStr,field_validator,model_validator,ConfigDict
from datetime import datetime
from models.user import Role

class UserRegistration(BaseModel):
    email:EmailStr
    password:str
    confirm_password:str
    role:Role=Role.user
    admin_secret_key:str|None=None

    @field_validator("password")
    @classmethod
    def password_min_length(cls,v):
        if len(v)<8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @model_validator(mode="after")
    def require_key_for_admin(self):
        if self.role==Role.admin and not self.admin_secret_key:
            raise ValueError("admin_secret_key is required to register as admin!")
        return self

class UserOut(BaseModel):
    id:int
    email:str
    role:Role
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email:EmailStr|None=None
    password:str|None=None
    role:Role|None=None
    admin_secret_key:str|None=None
    @model_validator(mode="after")
    def require_key_for_admin(self):
        if self.role==Role.admin and not self.admin_secret_key:
            raise ValueError("admin_secret_key is required to upgrade to admin role!")
        return self


class Token(BaseModel):
    access_token:str
    refres_token:str
    token_type:str="bearer"

class RefreshRequest(BaseModel):
    refresh_token:str

    
        