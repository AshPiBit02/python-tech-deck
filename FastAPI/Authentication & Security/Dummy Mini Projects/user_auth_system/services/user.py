from sqlalchemy.orm import Session
from models.user import User,Role
from schemas.user import UserRegistration,UserUpdate
from core.security import hash_password

def get_user_by_email(db:Session,email:str)->User|None:
    return db.query(User).filter(User.email==email).first()

def get_user_by_id(db:Session,user_id:int)->User|None:
    return db.query(User).filter(User.id==user_id).first()

def get_all_users(db:Session)->list[User]:
    return db.query(User).all()

