from fastapi import APIRouter,Depends,HTTPException
from dependencies.db_dependency import database_dependency
from models import User
from schemas.user import UserOut,UserUpdate
from services.user import get_all_users,get_user_by_id,update_user,delete_user
from dependencies.auth import get_current_user,require_admin

router=APIRouter(tags=["users"])

@router.get("/me",response_model=UserOut)
def read_me(current_user:User=Depends(get_current_user)):
    return current_user

@router.patch("/me",response_model=UserOut)
def update_me(db:database_dependency,body:UserUpdate,current_user:User=Depends(get_current_user)):
    role_changed=body.role is not None and body.role!=current_user.role
    updated_user=update_user(db,current_user.id,body)

    if role_changed:
        raise HTTPException(status_code=200,detail="Role updated. Please log in again to receive a token with new role.")
    return update_user

@router.get("/admin/users",response_model=list[UserOut])
def list_users(db:database_dependency,admin_user:User=Depends(require_admin)):
    return get_all_users(db)

@router.delete("/admin/users/{user_id}")
def remove_user(db:database_dependency,user_id:int,admin_user:User=Depends(require_admin)):
    deleted=delete_user(db,user_id)
    if not deleted:
        raise HTTPException(status_code=404,detail="User not found")
    return deleted
