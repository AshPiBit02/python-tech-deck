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

@router.get("/{user_id}",responses_model=User)
def get_user(user_id:int):
    user=users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found!")
    return User

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id:int):
    if user_id not in users_db:
        raise HTTPException(status_code=404,detail="User not found")
    del users_db[user_id]