from fastapi import APIRouter,HTTPException,status
from models import User,UserCreate

router=APIRouter(prefix="/users",tags=["Users"])

users_db:dict[int,User]={}
next_id=1

@router.post("/",response_model=User,status_code=status.HTTP_201_CREATED)
def create_user(payload:UserCreate):
    global next_id
    user=User(id=next_id,**payload.model_dump())
    users_db[user.id]=user
    next_id+=1
    return user

@router.get("/",response_model=list[User])
def list_users():
    return list(users_db.values())

