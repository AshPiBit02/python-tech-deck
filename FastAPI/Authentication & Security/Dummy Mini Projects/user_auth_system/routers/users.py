from fastapi import APIRouter,Depends,HTTPException
from dependencies.db_dependency import database_dependency
from models import User
from schemas.user import UserOut,UserUpdate
from services.user import get_all_users,get_user_by_id,update_user,delete_user
from dependencies.auth import get_current_user,require_admin,require_pin

router=APIRouter(tags=["users"])

@router.get("/me",response_model=UserOut)
def read_me(current_user:User=Depends(get_current_user)):
    return current_user

@router.get("/admin/user",reponse_model=UserOut)
def user_by_id(db:database_dependency,user_id:int,admin_user:User=Depends(require_admin)):
    user=get_user_by_id(db,user_id)
    if user is None:
        raise HTTPException(status_code=404,detail=f"User with id {user_id} not found!")
    return user

@router.patch("/me")
def update_me(db:database_dependency,body:UserUpdate,pin:str=Depends(require_pin),current_user:User=Depends(get_current_user)):
    role_changed=body.role is not None and body.role!=current_user.role
    updated_user=update_user(db,current_user.id,body,pin)
    response=UserOut.model_validate(updated_user).model_dump()
    if role_changed:
        response["notice"]="Role updated. Please log in again to receive a token with new role."
    return response

@router.get("/admin/users",response_model=list[UserOut])
def list_users(db:database_dependency,admin_user:User=Depends(require_admin)):
    return get_all_users(db)

@router.delete("/admin/users/{user_id}")
def remove_user(db:database_dependency,user_id:int,pin:str=Depends(require_pin),admin_user:User=Depends(require_admin)):
    deleted=delete_user(db,user_id,pin)
    if not deleted:
        raise HTTPException(status_code=404,detail="User not found")
    return deleted
