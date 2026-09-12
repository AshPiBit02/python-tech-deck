from sqlalchemy.orm import Session
from models.user import User,Role
from schemas.user import UserRegistration,UserUpdate
from core.security import hash_password
from dependencies.auth import verify_admin_key

def get_user_by_email(db:Session,email:str)->User|None:
    return db.query(User).filter(User.email==email).first()

def get_user_by_id(db:Session,user_id:int)->User|None:
    return db.query(User).filter(User.id==user_id).first()

def get_all_users(db:Session)->list[User]:
    return db.query(User).all()

def create_user(db:Session,user_in:UserRegistration)->User:
    if user_in.admin_secret_key is not None:
        verify_admin_key(user_in.admin_secret_key)

    bcrypt_password=hash_password(user_in.password)
    db_user=User(
        email=user_in.email,
        hashed_password=bcrypt_password,
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
        if key=="role":
            if value==Role.admin:
                verify_admin_key(user_in.admin_secret_key)
            setattr(db_user,key,value)
        elif key=="password":
            setattr(db_user,"hashed_password",hash_password(value))
        else:
            setattr(db_user,key,value)
    db.commit()
    db.refresh(db_user)
    return db_user