from db.database import Base
from sqlalchemy import (
    Column,Integer,String,DateTime,ForeignKey,Boolean,func,
)

class RefreshToken(Base):
    __tablename__="refresh_tokens"
    id=Column(Integer,primary_key=True,index=True)
    token=Column(String(512),unique=True,nullable=False,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),nullable=False)
    revoked=Column(Boolean,default=False,nullable=False)
    created_at=Column(DateTime,server_default=func.now())