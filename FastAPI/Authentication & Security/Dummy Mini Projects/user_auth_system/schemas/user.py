from pydantic import BaseModel,EmailStr,field_validator,model_validator
from datetime import datetime
from models.user import Role
from core.config import settings

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
            raise ValueError("admin_secret_key is required to register as admin")
        elif self.admin_secret_key!=settings.admin_secret_key:
            raise ValueError("admin key didn't match")
        