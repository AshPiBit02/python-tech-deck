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

def create_user(db:Session,user_in:UserRegistration)->User:
    hash_password=hash_password(user_in.password)
    db_user=User(
        email=user_in.email,
        hash_password=hash_password,
        role=user_in.role,
        )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db:Session,user_id:int,user_in:UserUpdate)->User:
    db_user=get_user_by_id(db,user_id)
    if not db_user:
        return None

    update_data=user_in.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        if key=="password":
            setattr(db_user,"hashed_password",hash_password(value))
        elif key=="role":

        else:
            setattr(db_user,key,value)
    db.commit()
    db.refresh(db_user)
    return db_user