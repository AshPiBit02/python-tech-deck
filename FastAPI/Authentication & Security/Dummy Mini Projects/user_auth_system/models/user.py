from db.database import Base
from sqlalchemy import (Column,INTEGER,String,func,DateTime)
from enum import Enum as PyEnum
from sqlalchemy.types import Enum
class Role(str,PyEnum):
    super_admin="Super Admin"
    admin="Admin"
    user="User"
    guest="Guest"
class User(Base):
    __tablename__="users"
    id=Column(INTEGER,primary_key=True,index=True)
    email=Column(String(255),unique=True,nullable=False)
    hashed_password=Column(String(128),nullable=False)
    role=Column(Enum(Role),nullable=False)
    created_at=Column(DateTime,server_default=func.now())